FROM flickpp/casket:latest

RUN mkdir app
ENV PYTHONPATH /app
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ARG SERVICE_NAME

COPY framework framework
COPY lib lib
COPY clients clients
COPY schemas.py schemas.py

COPY $SERVICE_NAME $SERVICE_NAME
RUN ln -v ${SERVICE_NAME}/service.py service.py

CMD ["casket", "service:app"]
