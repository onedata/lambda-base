__copyright__ = "Copyright (C) 2022-2023 ACK CYFRONET AGH"
__license__ = "MIT license cited in 'LICENSE.txt'."

import io
import json
import os
import sys
import time
import traceback
import uuid
from datetime import datetime

import requests

# handler is a module user provides when building final lambda image
# (using lambda-base as parent image)
from function import handler


HEARTBEAT_TIMEOUT_SEC = 10

FIRST_HEARTBEAT_RETRIES = 10
FIRST_HEARTBEAT_RETRY_DELAY_SEC = 5


class FirstHeartbeatDeliveryFailedError(Exception):
    pass


def handle_request():
    # Redirect stdout/stderr to /tmp/lambda.out to not incorporate accidental prints
    # into response (OpenFaaS treats anything written to stdout/stderr as part
    # of a response).
    tmp_out = open("/tmp/lambda.out", "a")
    tmp_out_fd = tmp_out.fileno()

    stdout_fd = sys.stdout.fileno()
    stdout_fd_dup = os.dup(stdout_fd)
    os.dup2(tmp_out_fd, stdout_fd)  # $ exec >&tmp_out_fd

    stderr_fd = sys.stderr.fileno()
    os.dup2(tmp_out_fd, stderr_fd)  # $ exec 2>&tmp_out_fd

    stdout_dup = io.TextIOWrapper(os.fdopen(stdout_fd_dup, "wb"))

    trace_id = uuid.uuid4()
    log(f"[INFO] Started request (id: {trace_id}) processing")

    try:
        request = json.loads(read_stdin())
        heartbeat_callback = build_heartbeat_callback(request["ctx"])

        # IMPORTANT: first heatbeat must be sent immediately after spawn
        # to inform Oneprovider that given job began executing
        ensure_first_heartbeat_delivered(heartbeat_callback)

        log("[INFO] Calling handler callback")
        result = handler.handle(request, heartbeat_callback)
        log(f"[INFO] Ended request (id: {trace_id}) processing")
        print(json.dumps(result), file=stdout_dup)

    except FirstHeartbeatDeliveryFailedError:
        log(
            f"[ERROR] Request (id: {trace_id}) processing failed due to "
            "failure to deliver first heartbeat"
        )
        print(
            json.dumps({"exception": "Failed to deliver first heartbeat"}),
            file=stdout_dup,
        )

    except Exception as ex:
        log(
            f"[ERROR] Request (id: {trace_id}) processing failed with "
            "unexpected exception"
        )
        print(json.dumps({"exception": traceback.format_exc()}), file=stdout_dup)


def build_heartbeat_callback(ctx):
    heartbeat_url = ctx["heartbeatUrl"]
    throttle_period = 0.1 * ctx["timeoutSeconds"]
    last_heartbeat_timestamp = 0

    def heartbeat(*, timeout=HEARTBEAT_TIMEOUT_SEC) -> bool:
        nonlocal last_heartbeat_timestamp

        current_time = int(time.time())
        if current_time - last_heartbeat_timestamp > throttle_period:
            r = requests.post(url=heartbeat_url, data={}, timeout=timeout)
            if r.ok:
                last_heartbeat_timestamp = current_time
                log("[INFO] Heartbeat sent")
                return True
            else:
                log(
                    f"[WARNING] Failed to send heartbeat due to:\n"
                    f"> response code: {r.status_code}\n"
                    f"> response content: {r.content}"
                )
                return False

    return heartbeat


def ensure_first_heartbeat_delivered(heartbeat_callback):
    log("[INFO] Sending first heartbeat")
    for _ in range(FIRST_HEARTBEAT_RETRIES):
        if heartbeat_callback():
            break

        time.sleep(FIRST_HEARTBEAT_RETRY_DELAY_SEC)
    else:
        raise FirstHeartbeatDeliveryFailedError


def log(msg):
    print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S:%f"), msg)


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
