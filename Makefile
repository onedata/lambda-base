SLIM_IMG_TAG=v2
ONEDATAFS_IMAGE_TAG=v1

SLIM_IMG_DEV=docker.onedata.org/lambda-base-slim:$(SLIM_IMG_TAG)
ONEDATAFS_IMG_DEV=docker.onedata.org/lambda-base-onedatafs:$(ONEDATAFS_IMAGE_TAG)

SLIM_IMG_PUBLIC=onedata/lambda-base-slim:$(SLIM_IMG_TAG)
ONEDATAFS_IMG_PUBLIC=onedata/lambda-base-onedatafs:$(ONEDATAFS_IMAGE_TAG)

STATIC_ANALYSER_IMAGE=docker.onedata.org/python_static_analyser:v8


.PHONY: build-slim publish-slim build-onedatafs publish-onedatafs


build-slim-dev:
	docker build . -f slim/Dockerfile -t ${SLIM_IMG_DEV}


publish-slim-dev:
	docker push ${SLIM_IMG_DEV}


build-onedatafs-dev:
	docker build . -f onedatafs/Dockerfile -t ${ONEDATAFS_IMG_DEV}


publish-onedatafs-dev:
	docker push ${ONEDATAFS_IMG_DEV}


build-slim-public:
	docker build . -f slim/Dockerfile -t ${SLIM_IMG_PUBLIC}


publish-slim-public:
	docker push ${SLIM_IMG_PUBLIC}


build-onedatafs-public:
	docker build . -f onedatafs/Dockerfile -t ${ONEDATAFS_IMG_PUBLIC}


publish-onedatafs-public:
	docker push ${ONEDATAFS_IMG_PUBLIC}