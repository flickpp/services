#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json as js
import os

import pika

from clients.exceptions import CallFailed
from lib.doolally import validate as validate_json
from schemas.rabbitmq import (
    RabbitMessage,
    EmailMessage,
)

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


def queue(routing_key):
    connection = pika.BlockingConnection(CONNECTIONS_PARAMS)
    channel = connection.channel()

    channel.queue_declare(routing_key, durable=True)

    return connection, channel


def send(ctx, msg_type, payload):
    message = {
        "traceId": ctx.trace_id,
        "parentId": ctx.span_id,
        "type": msg_type,
        "payload": payload,
    }

    validate_json(message, RabbitMessage)

    try:
        conn, channel = queue('plantpot')
        channel.basic_publish(exchange='',
                              routing_key='plantpot',
                              body=js.dumps(message))

        conn.close()

    except pika.exceptions.AMQPError as exc:
        raise CallFailed(f'failed to send message to rabbit {exc}')


def send_email(ctx, email_addr, message, session_id=None):
    payload = {
        "emailAddr": email_addr,
        "message": message,
        "sessionId": session_id,
    }

    validate_json(payload, EmailMessage)

    send(ctx, 'email', payload)

