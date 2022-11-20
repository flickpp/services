#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pickle
import os
from collections import namedtuple
from time import time
from hashlib import md5
from base64 import b64encode, b64decode

import requests

from lib import xor_encrypt, traceparent
from lib.doolally import validate as validate_json, ValidationError
from clients.exceptions import CallFailed, BadResponsePayload
from schemas.kvstore import RetrieveKVValuesResp

KVSTORE_ADDR = os.environ.get('PLANTPOT_KVSTORE_ADDR', 'kvstore:8080')
INSERT_URL = f"http://{KVSTORE_ADDR}/insert"
RETRIEVE_URL = f"http://{KVSTORE_ADDR}/retrieve"

KvValue = namedtuple('KVValue', ('value', 'ttl'))


def insert(ctx, prefix, mapping, ttl):
    payload = []
    expiry_time = int(time()) + ttl

    for k, v in mapping.items():
        xor_key = os.urandom(32)
        value = xor_encrypt(xor_key, pickle.dumps(v))

        payload.append({
            "key": build_key(prefix, k),
            "value": str(b64encode(value), encoding='utf8'),
            "xorKey": xor_key.hex(),
            "expiryTime": expiry_time,
        })

    try:
        headers = {"Traceparent": traceparent(ctx)}
        resp = requests.post(INSERT_URL,
                             headers=headers,
                             json=dict(values=payload))
        if "X-Error" in resp.headers:
            raise Exception(resp.headers['X-Error'])

        if resp.status_code != 202:
            raise Exception("expected 202 response from kvstore insert")

    except Exception as exc:
        raise CallFailed(f"failed to insert to kv store {exc}")


def retrieve(ctx, prefix, *keys):
    values = {}
    now = int(time())

    for (key, val) in zip(keys, retrieve_req(ctx, prefix, *keys)):
        if val['value'] is None:
            # We didn't find it
            values[key] = KvValue(None, None)
            continue

        xor_key = bytes.fromhex(val['xorKey'])
        value = xor_encrypt(xor_key, b64decode(val['value']))
        value = pickle.loads(value)

        ttl = val['expiryTime'] - now

        values[key] = KvValue(value, ttl)

    return values


def retrieve_req(ctx, prefix, *keys):
    url = RETRIEVE_URL

    for (n, k) in enumerate(keys):
        if n == 0:
            url += f'?key={build_key(prefix, k)}'
        else:
            url += f'&key={build_key(prefix, k)}'

    try:
        headers = {"Traceparent": traceparent(ctx)}
        resp = requests.get(url, headers=headers)

        if "X-Error" in resp.headers:
            raise Exception(resp.headers['X-Error'])

        if resp.status_code != 200:
            raise Exception("expected 200 response status")

        body = resp.json()
        validate_json(body, RetrieveKVValuesResp)

        if len(body['values']) != len(keys):
            raise Exception("kvstore didn't return expected number of values")

        return body['values']

    except ValidationError as exc:
        raise BadResponsePayload(
            f"kvstore returned bad response payload {exc}")

    except Exception as exc:
        raise CallFailed(f'call to kvstore retrieve failed {exc}')


def build_key(prefix, key):
    key = bytes(prefix + key, encoding='utf8')
    return md5(key).digest().hex()
