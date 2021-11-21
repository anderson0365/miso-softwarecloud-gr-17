FROM alpine:3.13.6
COPY requirements.txt .
RUN apk update \
    && apk upgrade \
    && apk add --no-cache --virtual .build-deps build-base \
    && apk add ffmpeg postgresql-dev bash \
    && apk add python3 python3-dev py3-pip \
    && ln -s /usr/bin/python3 /usr/bin/python \ 
    && pip install --no-cache-dir -r requirements.txt --ignore-installed six \
    && pip install --no-cache-dir pydub gunicorn\
    && pip install --no-cache-dir boto3 \
    && apk del .build-deps \
    && rm -rf requirements.txt \
    && addgroup app && adduser -S -G app app
USER app
RUN mkdir -p /home/app/flaskr
WORKDIR /home/app/flaskr
COPY --chown=app:app . .
RUN mv wsgi.py \
    && cp config.yml ../ \
    && chmod 777 start-celery.sh start-flask.sh wait-for-it.sh