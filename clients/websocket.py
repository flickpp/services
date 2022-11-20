#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json as js
import os

import requests

from clients.exceptions import CallFailed
from lib.doolally import validate as validate_json, ValidationError
from schemas.websocket import EmailSentReq, WebSocketMessage, WebSocketReq

WEBSOCKET_ADDR = os.environ.get('PLANTPOT_WEBSOCKET_MSG_ADDR', 'websocket:8081')
WEBSOCKET_MSG_URL = f"http://{WEBSOCKET_ADDR}/msgs"


def send_message(ctx,
                 msg_type,
                 message,
                 session_ids=None,
                 user_ids=None,
                 login_ids=None):
    payload = {
        "sessionIds": session_ids or [],
        "userIds": user_ids or [],
        "loginIds": login_ids or [],
        "message": js.dumps({
            "type": msg_type,
            "traceId": ctx.trace_id,
            "parentId": ctx.span_id,
            "message": message,
        }),
    }

    validate_json(payload, WebSocketReq)
    resp = requests.post(WEBSOCKET_MSG_URL, json=payload)
    if 'X-Error' in resp.headers:
        raise CallFailed(resp.headers['X-Error'])

    if resp.status_code != 200:
        raise CallFailed("failed to sent request to websocket")



def email_message(ctx,
                  email_addr,
                  message,
                  session_ids=None,
                  user_ids=None,
                  login_ids=None):
    message = {
        "emailAddr": email_addr,
        "message": message,
    }

    send_message(ctx,
                 "email.message",
                 message,
                 session_ids,
                 user_ids,
                 login_ids)


