FROM flickpp/casket:latest

RUN mkdir app
ENV PYTHONPATH /app
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ARG SERVICE_NAME
ARG KVSALT_PATH

COPY $KVSALT_PATH kvsalt
ENV PLANTPOT_TEMPKV_KEY_SALT_PATH /app/kvsalt

COPY framework framework
COPY lib lib
COPY clients clients
COPY schemas.py schemas.py

COPY $SERVICE_NAME $SERVICE_NAME
WORKDIR $SERVICE_NAME

CMD ["casket", "service:app"]
