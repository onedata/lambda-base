# lambda-base

*lambda-base* is a docker image which should be used as base when building images to be used in automation lambdas.


# Creating lambda dockers using lambda-base

In order to create a docker image that can be used as a Onedata automation lambda, follow the instructions below:

1. Create a `Dockerfile` with the following content:
```
FROM docker.onedata.org/lambda-base:v1
```

> NOTE: the lambda-base image uses the ONBUILD directives to include files
with predefined names (see pt. 2 and 3) during the docker build process.
This is why the Dockerfile can be as simple as one line.

2. Create a file named exactly `handler.py` and place it in the same directory as the `Dockerfile`. Implement the handle function.
```
def handle(request):
    """Example 'echo' function returning its arguments."""
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
