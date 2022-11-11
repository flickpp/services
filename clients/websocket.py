import os
import json as js

from requests import post

from casket import logger

from lib.doolally import validate as validate_json, ValidationError
from schemas import WebsocketReq


WEBSOCKET_MSG_PARTS = os.environ.get("PLANTPOT_WEBSOCKET_MSG_HOST", "websocket:8081").split(':')
if len(WEBSOCKET_MSG_PARTS) == 2:
    WEBSOCKET_MSG_URL = f"http://{WEBSOCKET_MSG_PARTS[0]}:{WEBSOCKET_MSG_PARTS[1]}/msgs"
elif len(WEBSOCKET_MSG_PARTS) == 1:
    WEBSOCKET_MSG_URL = f"http://{WEBSOCKET_MSG_PARTS[0]}:8081/msgs"
else:
    raise ValueError("invalid PLANTPOT_WEBSOCKET_MSG_HOST")



def send_login_ids(login_ids, msg_type, message, schema=None):
    if schema:
        try:
            validate_json(message, schema)
        except ValidationError as exc:
            logger.error("invalid websocket message schema", {
                "error": str(exc),
            })
            return

    send({
        "loginIds": login_ids,
        "userIds": [],
        "sessionIds": [],
        "message": js.dumps({"type": msg_type, "message": message}),
    })


def send(payload):
    try:
        validate_json(payload, WebsocketReq)
    except ValidationError as exc:
        logger.error("sending invalid payload to websocket", {
            "error": str(exc),
        })
        return

    try:
        resp = post(WEBSOCKET_MSG_URL, json=payload)

        if "X-Error" in resp.headers:
            raise Exception(resp.headers['X-Error'])

        if resp.status_code != 200:
            raise Exception("received non 200 status code from websocket service")

    except Exception as exc:
        logger.error("failed to send message on websocket", {
            "error": str(exc),
        })


