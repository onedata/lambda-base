# lambda-base

*lambda-base* is a docker image which should be used as base when building images to be used in automation lambdas.


# Using

To create final image useable in automation lambdas:

1. Create *Dockerfile* with *lambda-base* as base:
```
FROM docker.onedata.org/lambda-base:v1
```
2. Create *handler.py* with *handle* function:
```
def handle(request):
    ...
```
3. Optionally, if any external python dependencies are needed, create *requirements.txt*
4. Build and publish an image:
```
docker build . -t ${REPO}:${TAG}
docker push ${REPO}:${TAG}
```
5. Congratulations! Created image is ready to use in automation lambdas!


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
