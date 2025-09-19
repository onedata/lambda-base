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

VERIFY_SSL_CERTS = os.getenv("VERIFY_SSL_CERTIFICATES") == "true"
DEBUG_MODE = os.getenv("OPENFAAS_FUNCTION_DEBUG_MODE") == "true"
ONECLIENT_MOUNTED = os.getenv("ONECLIENT_MOUNTED") == "true"
ONECLIENT_MOUNT_POINT = os.getenv("ONECLIENT_MOUNT_POINT")

HEARTBEAT_TIMEOUT_SEC = 10

FIRST_HEARTBEAT_RETRIES = 10
FIRST_HEARTBEAT_RETRY_DELAY_SEC = 5

MOUNT_POINT_TIMEOUT = 120
MOUNT_POINT_TIMEOUT_INTERVAL = 0.5


class FirstHeartbeatDeliveryFailedError(Exception):
    pass


class OneclientMountError(Exception):
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

    job_id = uuid.uuid4()
    log("info", job_id, "Started request processing")

    if DEBUG_MODE:
        log("debug", job_id, "Lambda is running in debug mode")

    try:

        validate_oneclient_mount(job_id)

        request = json.loads(read_stdin())

        log_level = request["ctx"].get("logLevel", "info")
        os.environ["ATM_LOG_LEVEL"] = log_level

        if log_level == "debug":
            log("debug", job_id, f"Input: {request}")

        heartbeat_callback = build_heartbeat_callback(job_id, request["ctx"])

        # IMPORTANT: first heatbeat must be sent immediately after spawn
        # to inform Oneprovider that given job began executing
        ensure_first_heartbeat_delivered(job_id, heartbeat_callback)

        log("info", job_id, "Calling handler callback")

        # handler is a module user provides when building final lambda image
        # (using lambda-base as parent image)
        from function import handler

        result = handler.handle(request, heartbeat_callback)

        if log_level == "debug":
            log("debug", job_id, f"Output: {request}")

        log("info", job_id, "Ended request processing")

        print(json.dumps(result), file=stdout_dup)

    except FirstHeartbeatDeliveryFailedError:
        log(
            "error",
            job_id,
            f"Request processing failed due to failure to deliver first heartbeat",
        )
        print(
            json.dumps({"exception": "Failed to deliver first heartbeat"}),
            file=stdout_dup,
        )

    except OneclientMountError:
        log(
            "error",
            job_id,
            f"Request processing failed due to failure to mount Oneclient",
        )
        print(json.dumps({"exception": "Failed to mount Oneclient"}), file=stdout_dup)

    except Exception as ex:
        log(
            "error",
            job_id,
            f"Request processing failed with unexpected exception: {ex}",
        )
        print(json.dumps({"exception": traceback.format_exc()}), file=stdout_dup)


def build_heartbeat_callback(job_id, ctx):
    heartbeat_url = ctx["heartbeatUrl"]
    throttle_period = 0.1 * ctx["timeoutSeconds"]
    last_heartbeat_timestamp = 0

    def heartbeat(*, timeout=HEARTBEAT_TIMEOUT_SEC) -> bool:
        nonlocal last_heartbeat_timestamp

        current_time = int(time.time())
        if current_time - last_heartbeat_timestamp > throttle_period:
            r = requests.post(
                url=heartbeat_url, data={}, timeout=timeout, verify=VERIFY_SSL_CERTS
            )
            if r.ok:
                last_heartbeat_timestamp = current_time
                log("info", job_id, "Heartbeat sent")
                return True
            else:
                log(
                    "warning",
                    job_id,
                    f"Failed to send heartbeat due to:\n"
                    f"> response code: {r.status_code}\n"
                    f"> response content: {r.content}",
                )
                return False

    return heartbeat


def ensure_first_heartbeat_delivered(job_id, heartbeat_callback):
    log("info", job_id, "Sending first heartbeat")
    for _ in range(FIRST_HEARTBEAT_RETRIES):
        if heartbeat_callback():
            break

        time.sleep(FIRST_HEARTBEAT_RETRY_DELAY_SEC)
    else:
        raise FirstHeartbeatDeliveryFailedError


def validate_oneclient_mount(job_id):
    if ONECLIENT_MOUNTED:
        log(
            "info",
            job_id,
            f"This lambda is using Oneclient; mountpoint: {ONECLIENT_MOUNT_POINT}",
        )
        # wait for oneclient mounting
        if not await_oneclient_mounted():
            log("error", job_id, f"Did not manage to mount Oneclient")
            raise OneclientMountError
        else:
            log(
                "info",
                job_id,
                f"Oneclient mount point content: {list_mountpoint()}",
            )
    else:
        log("info", job_id, "This lambda is not using Oneclient")


def await_oneclient_mounted():
    retries = int(MOUNT_POINT_TIMEOUT / MOUNT_POINT_TIMEOUT_INTERVAL)
    mount_point_content = list_mountpoint()
    while not mount_point_content and retries > 0:
        time.sleep(MOUNT_POINT_TIMEOUT_INTERVAL)
        mount_point_content = list_mountpoint()
        retries -= 1
    return any(mount_point_content)


def list_mountpoint():
    return os.listdir(ONECLIENT_MOUNT_POINT)


def log(severity, job_id, msg):
    print(
        "[",
        severity.upper(),
        " ",
        datetime.now().strftime("%m/%d/%Y, %H:%M:%S:%f"),
        " ",
        job_id,
        "] ",
        msg,
        sep="",
    )


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
