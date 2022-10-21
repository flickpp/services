import os
import struct
from time import time

from casket import logger

from framework import app, post_json_endpoint, EmptyResponse, get_json_endpoint
from schemas import ContactByEmailReq, ContactByNumberReq, ContactQueryResp
from tempkv import tempkv_client, TempKvException


THROTTLE_TIMEOUT = int(os.environ.get("PLANTPOT_TULIPTHECLOWN_MESSAGE_TIMEOUT", 7200))


class Throttle:
    def __init__(self):
        try:
            self._kv_client = tempkv_client()
        except TempKvException:
            self._kv_client = None
            logger.warn("couldn't open tempkv client - there is no throttle")

    def mget(self, *keys):
        if self._kv_client is None:
            return [None] * len(keys)

        try:
            return self._kv_client.mget(*keys)
        except TempKvException as exc:
            logger.warn("couldn't get keys in tempkv client - there is no throttle", {
                "error": str(exc),
            })
            self._kv_client = None
            return [None] * len(keys)

    def get(self, key):
        return self.mget(key)[0]

    def mset(self, mapping):
        if self._kv_client is None:
            return

        try:
            self._kv_client.mset(mapping)
        except TempKvException as exc:
            logger.warn("couldn't set keys in tempkv client - there is no throttle", {
                "error": str(exc),
            })
            self._kv_client = None


def current_time():
    now = int(time())
    return struct.pack("<L", now)


def time_left(creation_time):
    creation_time = struct.unpack("<L", creation_time)[0]
    time_elapsed = int(time()) - creation_time
    return max(0, THROTTLE_TIMEOUT - time_elapsed)


def contact_by_email(session_id, body, **params):
    throttle = Throttle()

    for val in throttle.mget(session_id, body['email']):
        if val is not None:
            return EmptyResponse("406 Already Created", [])

    logger.info("new contact", {
        "gdpr.email": body['email'],
        "gdpr.name": body['name'],
        "session_id": session_id,
    })

    now = current_time()
    throttle.mset({
        session_id: now,
        body['email']: now,
    })

    return EmptyResponse("202 Accepted", [])


def contact_by_phone(session_id, body, **params):
    throttle = Throttle()

    for val in throttle.mget(session_id, body['number']):
        if val is not None:
            return EmptyResponse("406 Already Created", [])

    logger.info("new contact", {
        "gdpr.phone": body['number'],
        "gdpr.name": body['name'],
        "session_id": session_id,
    })

    now = current_time()
    throttle.mset({
        session_id: now,
        body['number']: now,
    })

    return EmptyResponse("202 Accepted", [])


def contact_query(session_id, **params):
    creation_time = Throttle().get(session_id)

    if creation_time is None:
        time_remaining = 0
    else:
        time_remaining = time_left(creation_time)

    return {
        "timeRemaining": time_remaining,
    }


post_json_endpoint("/contact/byemail", ContactByEmailReq, contact_by_email)
post_json_endpoint("/contact/byphone", ContactByNumberReq, contact_by_phone)
get_json_endpoint("/contact", ContactQueryResp, contact_query)
