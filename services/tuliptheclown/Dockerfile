FROM flickpp/casket:latest

RUN mkdir app
ENV PYTHONPATH /app
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN mkdir /blobs

ARG SERVICE_NAME

COPY framework framework
COPY plantpot plantpot
COPY lib lib
COPY clients clients
COPY models models
COPY schemas schemas

COPY services/tuliptheclown tuliptheclown

CMD ["casket", "tuliptheclown/tuliptheclown:app"]
