# lambda-base

*lambda-base* is a docker image which should be used as base when building images to be used in automation lambdas.
Available images:
- `lambda-base-slim:v1` - minimal debian based image with python 3.10 installed.
- `lambda-base-onedatafs:v1` - ubuntu based image with additional packages such as Oneclient and OnedataFS installed.


# Creating lambda dockers using lambda-base

In order to create a docker image that can be used as a Onedata automation lambda, follow the instructions below:

1. Create a `Dockerfile` with the following content:
```
FROM docker.onedata.org/lambda-base-slim:v1
```

or, when in need of OnedataFS:

```
FROM docker.onedata.org/lambda-base-onedatafs:v1
```

> NOTE: the lambda-base image uses the ONBUILD directives to include files
with predefined names (see pt. 2 and 3) during the docker build process.
This is why the Dockerfile can be as simple as one line.

2. Create a file named exactly `handler.py` and place it in the same directory as the `Dockerfile`. Implement the handle function.
```
def handle(request, heartbeat_callback):
    """Example 'echo' function returning its arguments."""

    # periodically call heartbeat_callback for long running jobs. 
    # Otherwise, if no heartbeat is sent for londer than 
    # `request["ctx"]["timeoutSeconds"]`, job will be considered as dead
    heartbeat_callback()

    return {'resultsBatch': request['argsBatch']}
```

3. Optionally, if any external python dependencies are needed, create a file named exactly `requirements.txt` and place it alongside the `Dockerfile`.

4. Build and publish an image:
```
docker build . -t ${REPO}:${TAG}
docker push ${REPO}:${TAG}
```

5. Congratulations! Created image is ready to be used in automation lambdas!


# Building
To build use the provided Makefile script:
```
make build
```


# Publishing
To publish use the provided Makefile script:
```
make publish
```
