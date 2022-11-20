#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json as js
import os
from datetime import datetime
from collections import namedtuple
from time import sleep

import pika

from schemas.rabbitmq import RabbitMessage, EmailMessage, RABBIT_MSG_TYPES
from clients.websocket import email_message as ws_email_message
from lib import traceparent
from lib.doolally import validate as validate_json, ValidationError

Context = namedtuple('Context', ('trace_id', 'parent_id', 'span_id'))

RABBITMQ_HOST = os.environ.get("PLANTPOT_RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.environ.get("PLANTPOT_RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.environ.get('PLANTPOT_RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD_PATH = os.environ.get("PLANTPOT_RABBITMQ_PASSWORD_PATH",
                                        "/run/secrets/rabbitmqpassword")
RABBITMQ_PASSWORD = open(RABBITMQ_PASSWORD_PATH).read()

AMQP_URL = f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"
CONNECTIONS_PARAMS = pika.URLParameters(AMQP_URL)
PROPERTIES = pika.BasicProperties(
    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE)


class Logger:

    def __init__(self, ctx):
        self._ctx = ctx

    def log(self, level, msg, tags=None):
        tags = tags or {}
        log_line = {
            "ts": datetime.now().isoformat(),
            "level": level,
            "msg": msg,
            **tags,
            "trace_id": self._ctx.trace_id,
            "parent_id": self._ctx.parent_id,
            "span_id": self._ctx.span_id,
        }

        print(js.dumps(log_line), flush=True)

    def info(self, msg, tags=None):
        self.log("info", msg, tags)

    def error(self, msg, tags=None):
        self.log("error", msg, tags)


def email(ctx, logger, payload):
    logger.info("sent email", tags={
        "gdpr.email_addr": payload['emailAddr'],
    })

    if payload['sessionId']:
        ws_email_message(ctx,
                         payload['emailAddr'],
                         payload['message'],
                         session_ids=[payload['sessionId']])


ACTIONS = {
    'email': email,
}

for msg_type in RABBIT_MSG_TYPES:
    assert msg_type in ACTIONS, f"missing msg type {msg_type}"


def callback(ch, method, properties, body):
    if method.routing_key != 'plantpot':
        raise RuntimeError('only plantpot queue should be tailed')

    body = js.loads(body)
    validate_json(body, RabbitMessage)
    ctx = Context(body['traceId'], body['parentId'], os.urandom(8).hex())
    logger = Logger(ctx)

    try:
        ACTIONS[body['type']](ctx, logger, body['payload'])
    except Exception as exc:
        logger.error("failed to handle message", tags={
            "error": str(exc),
        })
    else:
        ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    ch = pika.BlockingConnection(CONNECTIONS_PARAMS).channel()
    ch.queue_declare('plantpot', durable=True)
    ch.basic_consume(queue='plantpot', on_message_callback=callback)
    ch.start_consuming()


if __name__ == '__main__':
    while True:
        try:
            main()

        except KeyboardInterrupt:
            break

        except Exception as exc:
            msg = js.dumps({
                "ts": datetime.now().isoformat(),
                "level": "error",
                "error": str(exc)
            })
            print(msg, flush=True)
            sleep(5)
