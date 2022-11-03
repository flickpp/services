from os import environ
from hashlib import sha256

import requests


MONSTERMAC_HOST = environ.get("PLANTPOT_MONSTERMAC_HOST", "monstermac:8081")
MONSTERMAC_URL = f"http://{MONSTERMAC_HOST}"


class MonsterMacExc(Exception):
    pass


def sha256_monstermac(value):
    try:
        mm = monstermac(value)
    except Exception as exc:
        raise MonsterMacExc(str(exc))

    return sha256(mm).digest()
        


def monstermac(value):
    if isinstance(value, str):
        value = bytes(value, encoding='utf8')

    if not isinstance(value, (bytes, bytearray)):
        raise TypeError("value must be bytes or str")

    resp = requests.post(MONSTERMAC_URL)
    if resp.status_code != 200:
        raise Exception("expected 200 response code")

    return resp.content
