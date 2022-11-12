#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json as js
from time import sleep

from casket import logger

import pika

RABBITMQ_HOST = os.environ.get("PLANTPOT_RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.environ.get("PLANTPOT_RABBITMQ_PORT", "5672"))

CONNECTIONS_PARAMS = pika.ConnectionParameters(RABBITMQ_HOST, port=RABBITMQ_PORT)
PROPERTIES = pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)


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

