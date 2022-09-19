__copyright__ = "Copyright (C) 2022 ACK CYFRONET AGH"
__license__ = "MIT license cited in 'LICENSE.txt'."

import io
import json
import os
import sys
import threading
import time

from contextlib import contextmanager
import requests

# handler is a module user provides when building final lambda image 
# (using lambda-base as parent image)
from function import handler


HEARTBEAT_INTERVAL_SEC: int = 60


def handle_request(stdout):
    try:
        request = json.loads(read_stdin())
        heartbeat = build_heartbeat_fun(request["ctx"]["heartbeatUrl"])

        # IMPORTANT: first heatbeat must be sent immediately after spawn 
        # to inform Oneprovider that given job began executing
        heartbeat()

        result = handler.handle(request, heartbeat)

        print(json.dumps(result), file=stdout)

    except Exception as ex:
        print(json.dumps({"exception": str(ex)}), file=stdout)


def build_heartbeat_fun(heartbeat_url):
    last_heartbeat_timestamp = 0
    
    def heartbeat():
        nonlocal last_heartbeat_timestamp

        current_time = int(time.time())
        if current_time - last_heartbeat_timestamp > HEARTBEAT_INTERVAL_SEC:
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
    devnull = open(os.devnull, 'w')
    devnull_fd = devnull.fileno()

    stdout_fd = sys.stdout.fileno()
    stdout_fd_dup = os.dup(stdout_fd)
    os.dup2(devnull_fd, stdout_fd)   # $ exec >&devnull_fd

    stderr_fd = sys.stderr.fileno()
    os.dup2(devnull_fd, stderr_fd)   # $ exec 2>&devnull_fd

    handle_request(io.TextIOWrapper(os.fdopen(stdout_fd_dup, 'wb')))
