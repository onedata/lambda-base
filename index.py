__copyright__ = "Copyright (C) 2022 ACK CYFRONET AGH"
__license__ = "MIT license cited in 'LICENSE.txt'."

import io
import json
import os
import sys
import time

import requests

# handler is a module user provides when building final lambda image 
# (using lambda-base as parent image)
from function import handler


def handle_request():
    # Redirect stdout/stderr to /dev/null to not incorporate accidental prints 
    # into response (OpenFaaS treats anything written to stdout/stderr as part 
    # of a response). 
    devnull = open(os.devnull, 'w')
    devnull_fd = devnull.fileno()

    stdout_fd = sys.stdout.fileno()
    stdout_fd_dup = os.dup(stdout_fd)
    os.dup2(devnull_fd, stdout_fd)   # $ exec >&devnull_fd

    stderr_fd = sys.stderr.fileno()
    os.dup2(devnull_fd, stderr_fd)   # $ exec 2>&devnull_fd

    stdout_dup = io.TextIOWrapper(os.fdopen(stdout_fd_dup, 'wb'))

    try:
        request = json.loads(read_stdin())
        heartbeat_callback = build_heartbeat_callback(request["ctx"])

        # IMPORTANT: first heatbeat must be sent immediately after spawn 
        # to inform Oneprovider that given job began executing
        heartbeat_callback()

        result = handler.handle(request, heartbeat_callback)
        print(json.dumps(result), file=stdout_dup)

    except Exception as ex:
        print(json.dumps({"exception": str(ex)}), file=stdout_dup)


def build_heartbeat_callback(ctx):
    heartbeat_url = ctx["heartbeatUrl"]
    throttle_period = 0.1 * ctx["timeoutSeconds"]
    last_heartbeat_timestamp = 0
    
    def heartbeat():
        nonlocal last_heartbeat_timestamp

        current_time = int(time.time())
        if current_time - last_heartbeat_timestamp > throttle_period:
            r = requests.post(url=heartbeat_url, data={})
            if r.ok:
                last_heartbeat_timestamp = current_time

    return heartbeat


def read_stdin():
    buf = ""
    while True:
        line = sys.stdin.readline()
        if line == "":
            break

        buf += line

    return buf


if __name__ == "__main__":
    handle_request()
