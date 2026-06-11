# syntax=docker/dockerfile:1.7
FROM --platform=${TARGETPLATFORM:-linux/amd64} ghcr.io/openfaas/classic-watchdog:0.1.5 AS watchdog
FROM --platform=${TARGETPLATFORM:-linux/amd64} python:3.12-slim

# OpenFaaS classic watchdog: bridges the HTTP request <-> the `fprocess` stdio.
COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog

# uv: the canonical installer/resolver. Kept in the *runtime* image (single-stage)
# so `build-lambda` can run `uv sync` during a lambda build, and so the image is a
# usable debugging environment (`docker run -it lambda-base-slim:v3 bash`).
# Pinned for reproducible base builds; bump deliberately.
COPY --from=ghcr.io/astral-sh/uv:0.11.19 /uv /usr/local/bin/uv

# gosu: lets `build-lambda` perform the apt-as-root -> uv-sync-as-app privilege
# transition for declarative system-packages within a single RUN.
RUN set -eux \
    && apt-get update \
    && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/*

# Non-root runtime user.
RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && mkdir -p /home/app \
    && chown -R app:app /home/app

# Build-time logic (uv flags, venv path, system-packages, privilege drop) is
# encapsulated in this script so per-lambda Dockerfiles never see it.
COPY build-lambda /usr/local/bin/build-lambda
RUN chmod +x /usr/local/bin/build-lambda

USER app
WORKDIR /home/app

# Thin, SDK-free runtime bootstrap (variant 2'); the frozen base<->entry-point seam.
COPY --chown=app:app index.py ./

# Runtime environment contract: the lambda venv lives at a fixed path and is first
# on PATH, so `python3` resolves to the venv interpreter that `build-lambda` populates.
# Set here (in the base) so per-lambda Dockerfiles carry no ENV of their own.
ENV UV_PROJECT_ENVIRONMENT="/home/app/.venv"
ENV VIRTUAL_ENV="/home/app/.venv"
ENV PATH="/home/app/.venv/bin:$PATH"

ENV fprocess="python3 index.py"
EXPOSE 8080

HEALTHCHECK --interval=3s CMD [ -e /tmp/.lock ] || exit 1

CMD ["fwatchdog"]
