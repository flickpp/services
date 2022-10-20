FROM flickpp/casket:latest

RUN mkdir app
ENV PYTHONPATH /app
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY doolally.py doolally.py
COPY schemas.py schemas.py
COPY tuliptheclown.py service.py

CMD ["casket", "service:app"]