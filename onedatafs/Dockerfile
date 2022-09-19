FROM --platform=${TARGETPLATFORM:-linux/amd64} ghcr.io/openfaas/classic-watchdog:0.1.5 as watchdog
FROM --platform=${TARGETPLATFORM:-linux/amd64} onedata/oneclient:21.02.0-alpha27

ARG TARGETPLATFORM

COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog

# Add non root user
RUN addgroup --system app && adduser --system --ingroup app app

USER app

RUN mkdir -p /home/app/python

ENV PATH=$PATH:/home/app/.local/bin:/home/app/python/bin/
ENV PYTHONPATH=$PYTHONPATH:/home/app/python

WORKDIR /home/app/

COPY --chown=app:app index.py requirements.txt ./
RUN python3 -m pip install --no-cache-dir --system -r requirements.txt -t /home/app/python

RUN mkdir -p function && touch ./function/__init__.py

# Copy required handler.py and optional requirements.txt if it exists 
# ('*' regex hack prevent build failure if file does not exist)
ONBUILD COPY --chown=app:app handler.py *requirements.txt function/
ONBUILD RUN if [ -e function/requirements.txt ]; then python3 -m pip install --no-cache-dir --system -r function/requirements.txt -t /home/app/python; else echo "No additional dependencies specified"; fi

ENV fprocess="python3 index.py"
EXPOSE 8080

HEALTHCHECK --interval=3s CMD [ -e /tmp/.lock ] || exit 1

ENTRYPOINT ["fwatchdog"]
