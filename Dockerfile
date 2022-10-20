FROM flickpp/casket:0.2

RUN mkdir app
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY doolally.py doolally.py
COPY schemas.py schemas.py
COPY tuliptheclown.py service.py

RUN ["casket", "service:app"]