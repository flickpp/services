#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json as js
import os
from time import sleep

import pika
from casket import logger

RABBITMQ_HOST = os.environ.get("PLANTPOT_RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.environ.get("PLANTPOT_RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.environ.get('PLANTPOT_RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD_PATH = os.environ.get("PLANTPOT_RABBITMQ_PASSWORD_PATH",
                                         "/run/secrets/rabbimqpassword")
RABBITMQ_PASSWORD = open(RABBITMQ_PASSWORD_PATH).read()

AMQP_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"
CONNECTIONS_PARAMS = pika.URLParameters(AMQP_URL)
PROPERTIES = pika.BasicProperties(
    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)


def create_queue(routing_key):
    connection = pika.BlockingConnection(CONNECTIONS_PARAMS)
    channel = connection.channel()

    channel.queue_declare(routing_key, durable=True)

    return connection, channel


def send_email(email_addr, body):
    try:
        conn, channel = create_queue('email')
        msg = js.dumps({"email": email_addr, "body": body})
        channel.basic_publish(exchange='', routing_key='email', body=msg)

        conn.close()
    except pika.exceptions.AMQPError as exc:
        logger.error("couldn't write email to rabbitmq", {
            "error": str(exc),
        })
