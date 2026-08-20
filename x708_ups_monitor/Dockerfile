ARG BUILD_FROM
FROM $BUILD_FROM

# Dépendances système : python3, i2c-tools (debug), libgpiod (pulse GPIO)
RUN apk add --no-cache \
        python3 \
        py3-pip \
        i2c-tools \
        libgpiod \
    && pip3 install --no-cache-dir --break-system-packages \
        smbus2 \
        requests \
        gpiod

COPY run.sh /run.sh
COPY x708_monitor.py /x708_monitor.py

RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
