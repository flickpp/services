import os
from hashlib import sha256
from base64 import b64encode, b64decode
from collections import namedtuple
from time import time

import requests
import skein

from casket import logger

from schemas import RetrieveKVValuesResp
from lib.doolally import validate as validate_json


KV_STORE_HOST = os.environ.get("PLANTPOT_KV_STORE_HOST", "kvstore:8080").split(':')
if len(KV_STORE_HOST) == 2:
    KV_STORE_PORT = int(KV_STORE_HOST[1])
    KV_STORE_HOST = KV_STORE_HOST[0]
elif len(KV_STORE_HOST) == 1:
    KV_STORE_HOST = KV_STORE_HOST[0]
    KV_STORE_PORT = 8080
else:
    raise ValueError("invalid PLANTPOT_KV_STORE_HOST value")


URL_INSERT = f"http://{KV_STORE_HOST}:{KV_STORE_PORT}/insert"
URL_RETRIEVE = f"http://{KV_STORE_HOST}:{KV_STORE_PORT}/retrieve"
XOR_KEY_LEN = 32
KEY_SALT_PATH = os.environ.get("PLANTPOT_TEMPKV_KEY_SALT_PATH", "/run/secrets/kvsalt")
KEY_SALT = open(KEY_SALT_PATH, 'rb').read()
XOR_KEY_ENC_PATH = os.environ.get("PLANTPOT_TEMPKV_ENC_KEY_PATH", "/run/secrets/kvenckey")
XOR_KEY_ENC = open(XOR_KEY_ENC_PATH, 'rb').read()

assert(len(XOR_KEY_ENC) == XOR_KEY_LEN), "XOR_KEY_ENC not same length as XOR_KEY_LEN"


KvValue = namedtuple("KvValue", ("key", "value", "expiry_time"))


def insert(ctx, mapping, ttl):
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
        xor_key_enc = skein.threefish(XOR_KEY_ENC, tweak).encrypt_block(xor_key).hex()

        values.append({
            "key": inner_key,
            "value": str(b64encode(value), encoding='utf8'),
            "xorKey": xor_key_enc,
            "expiryTime": expiry_time,
        })

    try:
        headers = {"Traceparent": traceparent(ctx)}
        resp = requests.post(URL_INSERT, json={"values": values}, headers=headers)
        if "x-error" in resp.headers:
            raise Exception(resp.headers['x-error'])

        if resp.status_code != 202:
            raise Exception("not 202 response code")

        return len(values)

    except Exception as exc:
        logger.error("couldn't insert values into k/v store", {
            "error": str(exc),
        })

        return 0


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

    for (key, val, tweak) in zip(keys, inner_values, inner_tweaks):
        if val is None or val['value'] is None:
            values.append(KvValue(key, None, None))
            continue

        xor_key_enc = bytes.fromhex(val['xorKey'])
        xor_key = skein.threefish(XOR_KEY_ENC, tweak).decrypt_block(xor_key_enc)
        val['value'] = b64decode(val['value'])
        val['value'] = xor_encrypt(xor_key, val['value'])

        val['key'] = key
        del val['xorKey']

        values.append(KvValue(key, val['value'], val['expiryTime']))

    return values
        

def retrieve_request(ctx, *keys):
    url = URL_RETRIEVE + '?'
    for n, k in enumerate(keys):
        if n != 0:
            url += '&'

        url += f"key={k}"

    try:
        resp = requests.get(url, headers={"Traceparent": traceparent(ctx)})
        if resp.status_code != 200:
            raise Exception("call to kvstore retrieve did not return 200 status code")

        body = resp.json()
        validate_json(body, RetrieveKVValuesResp)
        return body['values']

    except Exception as exc:
        logger.error("failed to retrieve keys from kvstore", {
            "error": str(exc),
        })

        return [None] * len(keys)


def xor_encrypt(xor_key, data):
    data = bytearray(data)

    for n in range(0, len(data)):
        data[n] ^= xor_key[n % XOR_KEY_LEN]

    return bytes(data)


def traceparent(ctx):
    return f"00-{ctx.trace_id}-{ctx.span_id}-00"
