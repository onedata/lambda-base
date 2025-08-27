SLIM_IMG=docker.onedata.org/lambda-base-slim:v2-dev
ONEDATAFS_IMG=docker.onedata.org/lambda-base-onedatafs:v1


.PHONY: build-slim publish-slim build-onedatafs publish-onedatafs


build-slim:
	docker build . -f slim/Dockerfile -t ${SLIM_IMG}


publish-slim:
	docker push ${SLIM_IMG}


build-onedatafs:
	docker build . -f onedatafs/Dockerfile -t ${ONEDATAFS_IMG}


publish-onedatafs:
	docker push ${ONEDATAFS_IMG}
