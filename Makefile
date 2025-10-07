SLIM_IMG=docker.onedata.org/lambda-base-slim:v2
ONEDATAFS_IMG=docker.onedata.org/lambda-base-onedatafs:v1
STATIC_ANALYSER_IMAGE=docker.onedata.org/python_static_analyser:v8


.PHONY: build-slim publish-slim build-onedatafs publish-onedatafs


build-slim:
	docker build . -f slim/Dockerfile -t ${SLIM_IMG}


publish-slim:
	docker push ${SLIM_IMG}


build-onedatafs:
	docker build . -f onedatafs/Dockerfile -t ${ONEDATAFS_IMG}


publish-onedatafs:
	docker push ${ONEDATAFS_IMG}

UID := $(shell id -u)
GID := $(shell id -g)

define docker_run
	docker run --rm -i -v $(CURDIR):$(CURDIR) -w $(CURDIR) -u $(UID):$(GID) $(STATIC_ANALYSER_IMAGE) $1
endef

format:
	$(docker_run) isort .
	$(docker_run) black .
