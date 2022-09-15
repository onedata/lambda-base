__copyright__ = "Copyright (C) 2022 ACK CYFRONET AGH"
__license__ = "MIT license cited in 'LICENSE.txt'."

import json
import os
import sys
import threading
import time

from contextlib import redirect_stdout, redirect_stderr
import requests

# handler is a module user provides when building final lambda image 
# (using lambda-base as parent image)
from function import handler


HEARTBEAT_INTERVAL_SEC: int = 60


def heartbeat(url):
    # IMPORTANT: first heatbeat must be sent immediately after spawn 
    # to inform Oneprovider that given job began executing
    requests.post(url=url, data={})

    while True:
        time.sleep(HEARTBEAT_INTERVAL_SEC)
        requests.post(url=url, data={})


def get_stdin():
    buf = ""
    while True:
        line = sys.stdin.readline()
        if line == "":
            break

        buf += line

    return buf


def handle_request(request):
    with open(os.devnull, 'w') as f, redirect_stdout(f), redirect_stderr(f):
        return handler.handle(request)
    

if __name__ == "__main__":
    request = json.loads(get_stdin())

    heartbeat_cron = threading.Thread(target=heartbeat, 
                                      args=[request["ctx"]["heartbeatUrl"]])
    heartbeat_cron.daemon = True
    heartbeat_cron.start()

    try:
        result = handler.handle(request)
        print(json.dumps(result))
    except Exception as ex:
        print(json.dumps({"exception": str(ex)}))
