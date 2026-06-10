SLIM_IMG_TAG=v3

SLIM_IMG_DEV=docker.onedata.org/lambda-base-slim:$(SLIM_IMG_TAG)
SLIM_IMG_PUBLIC=onedata/lambda-base-slim:$(SLIM_IMG_TAG)


.PHONY: build-slim-dev publish-slim-dev build-slim-public publish-slim-public format lint


build-slim-dev:
	docker build . -f slim/Dockerfile -t ${SLIM_IMG_DEV}


publish-slim-dev:
	docker push ${SLIM_IMG_DEV}


build-slim-public:
	docker build . -f slim/Dockerfile -t ${SLIM_IMG_PUBLIC}


publish-slim-public:
	docker push ${SLIM_IMG_PUBLIC}


# Lint/format the repo's own Python (index.py + the build-lambda script) with ruff via
# uvx, the same toolchain as onedata-lambda-utils. Config lives in ruff.toml.
format:
	uvx ruff format .
	uvx ruff check --fix .


lint:
	uvx ruff format --check .
	uvx ruff check .
