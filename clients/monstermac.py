#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from hashlib import sha256

import requests

from clients.exceptions import CallFailed


MONSTERMAC_ADDR = os.environ.get("PLANTPOT_MONSTERMAC_ADDR", "monstermac:8081")
URL = f"http://{MONSTERMAC_ADDR}"


def monstermac(value):
    if isinstance(value, str):
        value = bytes(value, encoding='utf8')

    if not isinstance(value, (bytes, bytearray)):
        raise TypeError("expected str or bytes for monstermac")

    try:
        resp = requests.post(URL, data=value)
        if 'X-Error' in resp.headers:
            raise Exception(resp.headers['X-Error'])

        if resp.status_code != 200:
            raise Exception('expected 200 status code from monstermac')

        return resp.content

    except Exception as exc:
        raise CallFailed(f'failed to call monstermac {exc}')


def sha256_monstermac(value):
    return sha256(monstermac(value)).digest()


def login_key(login_id):
    login_id = bytes.fromhex(login_id)
    return monstermac(login_id)[:16]
