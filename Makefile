SLIM_IMG_TAG=v3

SLIM_IMG_DEV=docker.onedata.org/lambda-base-slim:$(SLIM_IMG_TAG)
SLIM_IMG_PUBLIC=onedata/lambda-base-slim:$(SLIM_IMG_TAG)

.DEFAULT_GOAL := help
.PHONY: help build-slim-dev publish-slim-dev build-slim-public publish-slim-public \
        format format-check static-analysis type-check lint

bold := $(shell tput bold)
normal := $(shell tput sgr0)
blue := $(shell tput setaf 4)

define print_target
	@echo ""
	@echo "$(blue)$(bold)$@:$(normal)"
endef

# `make help` groups targets by `##@ section` banners and lists each `target: ## description`.
help:
	@awk 'BEGIN{FS=":.*## "} /^##@ /{printf "\n%s:\n",substr($$0,5)} /^[a-z][a-zA-Z0-9_-]*:.*## /{printf "  %-20s %s\n",$$1,$$2}' $(MAKEFILE_LIST)

##@ image

build-slim-dev: ## build the slim dev image
	docker build . -f slim/Dockerfile -t ${SLIM_IMG_DEV}

publish-slim-dev: ## push the slim dev image
	docker push ${SLIM_IMG_DEV}

build-slim-public: ## build the slim public image
	docker build . -f slim/Dockerfile -t ${SLIM_IMG_PUBLIC}

publish-slim-public: ## push the slim public image
	docker push ${SLIM_IMG_PUBLIC}

##@ checks

# Lint/format the repo's own Python (index.py + the build-lambda script) with ruff via
# uvx, the same toolchain as onedata-lambda-sdk. Config lives in ruff.toml.
format: ## ruff format + autofix
	$(call print_target)
	uvx ruff format .
	uvx ruff check --fix .

format-check: ## ruff format --check
	$(call print_target)
	uvx ruff format --check .

static-analysis: ## ruff check
	$(call print_target)
	uvx ruff check .

# Type-check the repo's own Python with mypy. Config lives in mypy.ini; build-lambda is
# an extensionless script so it's passed explicitly. Mirrors onedata-lambda-sdk.
type-check: ## mypy
	$(call print_target)
	uvx mypy index.py build-lambda

lint: format-check static-analysis type-check ## format-check + static-analysis + type-check
	@:
