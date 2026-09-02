# lambda-base

`lambda-base` is the Docker base image for building [Onedata Automation](https://onedata.org)
lambdas — the containers that run as job executors in automation workflows.

**Image:** `onedata/lambda-base-slim:v3` (dev registry: `docker.onedata.org/lambda-base-slim:v3`).

## How it works

Three layers, split by how often they change:

- **base image** (this repo) — OS, Python 3.12, `uv`, the OpenFaaS watchdog, the `app` user,
  the venv environment contract, a thin SDK-free `index.py` bootstrap, and the `build-lambda`
  script that encapsulates all build-time logic.
- **SDK** ([`onedata-lambda-sdk`](https://pypi.org/project/onedata-lambda-sdk/)) — the
  runtime contract (`run(handler, raw)`), the handler API (`Job`, `JobContext`), services
  (heartbeat, logger, result streaming) and test helpers. **Required** — you declare it as a
  dependency (the build fails without it); the base never installs it for you.
- **handler** — your code: a plain function registered as the single `onedata.lambda` entry point.

At runtime the base loads your entry point and the SDK's `run(handler, raw)` drives it. Any
failure is wrapped into a top-level `{"exception": …}` response.

## Writing a lambda

This section is a quick reference. The full authoring guides — the handler API,
testing, streaming, file access — live with the SDK, under `docs/` in
`onedata-lambda-sdk`.

### Single lambda, one repo

```
my-lambda/
├── Dockerfile          # copied from templates/Dockerfile — do not edit the build section
├── pyproject.toml
├── uv.lock
└── src/my_lambda/
    ├── __init__.py
    └── handler.py
```

`pyproject.toml` — the hard requirements are a package name, the `onedata-lambda-sdk`
dependency, and **exactly one** `onedata.lambda` entry point:

```toml
[project]
name = "my-lambda"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["onedata-lambda-sdk>=1.0"]

[project.entry-points."onedata.lambda"]
handler = "my_lambda.handler:handle"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Handler — write against the handler API and let the SDK adapt the wire request and wrap the
response:

```python
def handle(jobs, ctx):
    return [{"answer": 42} for _ in jobs]
```

Build:

```bash
cp /path/to/lambda-base/templates/Dockerfile .
docker build -t my-lambda:dev .
```

### Multiple lambdas + shared code (uv workspace)

A `[tool.uv.workspace]` repo with `lambdas/*` (deployables) and `packages/*` (shared libs), a
single root `uv.lock`, and one root `Dockerfile`. Build a specific member with a build arg — the
image gets only that lambda's dependency subtree:

```bash
docker build --build-arg LAMBDA_PACKAGE=fetch-data -t fetch-data:dev .
```

`automation-examples` is the canonical instance of this layout.

### System packages

Declare apt packages your lambda needs in its `pyproject.toml`; `build-lambda` installs them
(no `apt` lines in your Dockerfile):

```toml
[tool.onedata.lambda]
system-packages = ["libmagic1"]
```

## The canonical Dockerfile

[`templates/Dockerfile`](./templates/Dockerfile) is the single source of truth. You copy it once
and don't touch the build section — `uv` flags,
the venv path and the root→`app` privilege transition all live in `build-lambda` inside the base
image, so they evolve with a base-image bump, not a change in your repo.

Requires Docker ≥ 23 (BuildKit) for the `--mount` directives.

## Migrating a lambda from v2 to v3

1. Move `docker/handler.py` → `src/<name>/handler.py` and adapt it to the v3 handler API
   (`handle(jobs, ctx)`).
2. Create `pyproject.toml`: move `requirements.txt` entries into `dependencies` and add the
   `onedata.lambda` entry point. **Audit imports vs declared deps** — v2's base shipped
   `requests` globally, so REST lambdas often used it without declaring it; v3 prunes to what
   you declare, so add `requests` (and anything else) explicitly.
3. Copy `templates/Dockerfile`, commit a `uv.lock`, build.

## Building and publishing the base image

Run `make help` for the full target list.

```bash
make build-slim-dev        # build docker.onedata.org/lambda-base-slim:v3
make publish-slim-dev      # push it
make build-slim-public     # build onedata/lambda-base-slim:v3
make publish-slim-public   # push it
make format                # ruff format + ruff check --fix
make lint                  # ruff format --check + ruff check + mypy (CI gate)
```
