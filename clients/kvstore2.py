#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json as js
from collections import namedtuple
from time import time
from hashlib import sha256
from base64 import b64encode, b64decode

import requests
import skein

from lib import xor_encrypt, traceparent
from lib.doolally import validate as validate_json, ValidationError
from schemas.kvstore import RetrieveKVValuesResp

from clients.exceptions import CallFailed, BadResponsePayload

KVSTORE_ADDR = os.environ.get('PLANTPOT_KVSTORE_ADDR', 'kvstore:8080')
KVSTORE_INSERT_URL = f"http://{KVSTORE_ADDR}/insert"
KVSTORE_RETRIEVE_URL = f"http://{KVSTORE_ADDR}/retrieve"

KEY_SALT_PATH = os.environ.get('PLANTPOT_TEMPKV_KEY_SALT_PATH',
                               '/run/secrets/kvsalt')
KEY_SALT = open(KEY_SALT_PATH, 'rb').read()
XOR_KEY_LEN = 32
XOR_KEY_ENC_PATH = os.environ.get('PLANTPOT_TEMPKV_ENC_KEY_PATH',
                                  '/run/secrets/kvenckey')
XOR_KEY_ENC = open(XOR_KEY_ENC_PATH, 'rb').read()

assert len(
    XOR_KEY_ENC) == XOR_KEY_LEN, "XOR_KEY_ENC not the same length as XOR_KEY"

KVValue = namedtuple('KVValue', ("key", "value", "expiry_time"))


def insert(ctx, mapping, ttl):
    if not mapping:
        return

    expiry_time = int(time()) + ttl

    values = []
    inner_keys = []
    inner_tweaks = []

    for k, v in mapping.items():
        pair = sha256(KEY_SALT + bytes(k, encoding='utf8')).digest()
        inner_key = pair[:16].hex()
        tweak = pair[16:]

        if isinstance(v, str):
            v = bytes(v, encoding='utf8')

        xor_key = os.urandom(XOR_KEY_LEN)
        value = xor_encrypt(xor_key, v)
        xor_key_enc = skein.threefish(XOR_KEY_ENC,
                                      tweak).encrypt_block(xor_key).hex()

        values.append({
            "key": inner_key,
            "value": str(b64encode(value)),
            "xorKey": xor_key_enc,
            "expiryTime": expiry_time,
        })

        headers = {"Traceparent": traceparent(ctx)}

        try:
            resp = requests.post(KVSTORE_INSERT_URL,
                                 json={"values": values},
                                 headers=headers)
            if "x-error" in resp.headers:
                raise Exception(resp.headers["x-error"])

            if resp.status_code != 202:
                raise Exception(
                    "kvstore insert didn't return 202 response code")

            return len(values)

        except Exception as exc:
            raise CallFailed(str(exc))


def retrieve(ctx, *keys):
    inner_keys = []
    inner_tweaks = []

    for k in keys:
        pair = sha256(KEY_SALT + bytes(k, encoding='utf8')).digest()
        inner_keys.append(pair[:16].hex())
        inner_tweaks.append(pair[16:])

    # retrieve the values
    inner_values = retrieve_request(ctx, *inner_keys)
    values = []

    for (key, inner_val, tweak) in zip(keys, inner_values, inner_tweaks):

        # didn't find value in k/v store
        if inner_val is None or inner_val['value'] is None:
            values.append(KVValue(key, None, None))
            continue

        xor_key_enc = bytes.fromhex(inner_val['xorKey'])
        xor_key = skein.threefish(XOR_KEY_ENC,
                                  tweak).decrypt_block(xor_key_enc)
        inner_val['value'] = b64decode(inner_val['value'])
        inner_val['value'] = xor_encrypt(xor_key, inner_val['value'])

        inner_val['key'] = key
        del inner_val['xorKey']

        values.append(KVValue(key, inner_val['value'],
                              inner_val['expiryTime']))

    return values


def retrieve_request(ctx, *inner_keys):
    url = KVSTORE_RETRIEVE_URL

    for (n, k) in enumerate(inner_keys):
        if n == 0:
            url += f"?key={k}"
        else:
            url += f"&key={k}"

    try:
        resp = requests.get(url, headers={"Traceparent": traceparent(ctx)})
        if "x-error" in resp.headers:
            raise Exception(resp.headers['x-error'])

        if resp.status_code != 200:
            raise Exception("kvstore retrieve didn't return 200 status code")

        body = resp.json()
        validate_json(body, RetrieveKVValuesResp)
        return body['values']

    except (ValidationError, js.JSONDecodeError) as exc:
        raise BadResponsePayload(str(exc))

    except Exception as exc:
        raise CallFailed(str(exc))
