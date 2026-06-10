"""Thin OpenFaaS bootstrap for Onedata Automation lambdas (lambda-base v3).

This file ships *inside the base image* and is deliberately minimal and frozen: the
lambda runtime contract lives in the SDK (`onedata-lambda-utils`), not here. The base
only:

  1. reads the raw request from stdin,
  2. loads the single `onedata.lambda` entry point declared by the lambda package,
  3. hands off to the SDK's `run(handler, raw)`.

The SDK is required; its presence is enforced at image build time by `build-lambda`. Any
failure here -- including, defensively, a broken SDK import -- is wrapped into a clean
top-level `{"exception": ...}` envelope rather than an opaque watchdog error,
consistent with Oneprovider's lambda error model.
"""

__author__ = "Bartosz Walkowicz"
__copyright__ = "Copyright (C) 2026 Onedata (onedata.org)"
__license__ = "This software is released under the MIT license cited in LICENSE.txt"

import importlib.metadata as importlib_metadata
import json
import sys
import traceback
from typing import Final

ENTRY_POINT_GROUP: Final[str] = "onedata.lambda"


def main() -> None:
    raw = sys.stdin.read()
    try:
        handler = load_handler()
        # The SDK is required (enforced at build time); a broken import here still lands
        # in the except below as a clean {"exception": ...} rather than a crash.
        from onedata_lambda_utils import run

        output = run(handler, raw)
        sys.stdout.write(json.dumps(output))
    except Exception:
        sys.stdout.write(json.dumps({"exception": traceback.format_exc()}))


def load_handler():
    entry_points = list(importlib_metadata.entry_points(group=ENTRY_POINT_GROUP))

    if not entry_points:
        raise RuntimeError(
            f"No entry point registered in group '{ENTRY_POINT_GROUP}'. Did you "
            f'forget [project.entry-points."{ENTRY_POINT_GROUP}"] in pyproject.toml?'
        )
    if len(entry_points) > 1:
        names = ", ".join(ep.name for ep in entry_points)
        raise RuntimeError(f"Multiple lambda entry points found ({names}); exactly one expected.")

    return entry_points[0].load()


if __name__ == "__main__":
    main()
