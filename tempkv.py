import os
from hashlib import sha256
from base64 import b64encode

import redis
import skein

from casket import logger

REDIS_BIND = os.environ.get("PLANTPOT_REDIS_HOST", "redis:6379").split(':')
if len(REDIS_BIND) == 2:
    REDIS_HOST = REDIS_BIND[0]
    REDIS_PORT = int(REDIS_BIND[1])
elif len(REDIS_BIND) == 1:
    REDIS_HOST = REDIS_BIND[0]
    REDIS_PORT = 6379
else:
    raise ValueError(f"invalid PLANTPOT_REDIS_BIND - [{':'.join(REDIS_BIND)}]")


class TempKvException(Exception):
    pass


class TempKvNotConnected(TempKvException):
    pass


class TempKvKeyError(TempKvException):
    pass


REDIS_CLIENT = None
XOR_KEY_LEN = 32
KEY_SALT_PATH = os.environ.get("PLANTPOT_TEMPKV_KEY_SALT_PATH", "/run/secrets/tempkvsalt")
KEY_SALT = open(KEY_SALT_PATH, 'rb').read()
XOR_KEY_ENC_PATH = os.environ.get("PLANTPOT_TEMPKV_ENC_KEY_PATH", "/run/secrets/tempkvenckey")
XOR_KEY_ENC = open(XOR_KEY_ENC_PATH, 'rb').read()

assert(len(XOR_KEY_ENC) == XOR_KEY_LEN)


class TempKvClient:
    def __init__(self, redis_client):
        self._redis_client = redis_client

    def mset(self, mapping):
        global REDIS_CLIENT, KEY_SALT, XOR_KEY_LEN
        new_map = {}

        for (key, value) in mapping.items():
            key_pair = sha256(KEY_SALT + bytes(key, encoding='utf8')).digest()
            xor_key_key = b64encode(key_pair[:16])
            value_key = b64encode(key_pair[16:])

            if isinstance(value, str):
                value = bytes(value, encoding='utf8')

            if not isinstance(value, (bytes, bytearray)):
                raise TypeError("temp kv value must be a byte-like object")

            xor_key = os.urandom(XOR_KEY_LEN)
            value = xor_value(xor_key, value)

            # encrypt the xor_key
            xor_key = skein.threefish(XOR_KEY_ENC, key_pair[16:]).encrypt_block(xor_key)

            new_map[xor_key_key] = xor_key
            new_map[value_key] = value

        try:
            self._redis_client.mset(new_map)
        except Exception as exc:
            logger.error("redis connection ended", {
                "error": str(exc),
            })
            REDIS_CLIENT = None
            raise TempKvNotConnected

    def set(self, key, value):
        return self.mset({key: value})

    def mget(self, *keys):
        global REDIS_CLIENT, KEY_SALT

        keys_inner = []
        key_pairs = []
        for key in keys:
            key_pair = sha256(KEY_SALT + bytes(key, encoding='utf8')).digest()
            xor_key_key = b64encode(key_pair[:16])
            value_key = b64encode(key_pair[16:])
            key_pairs.append(key_pair)
            keys_inner.extend((xor_key_key, value_key))

        try:
            values_inner = self._redis_client.mget(*keys_inner)
        except Exception as exc:
            logger.error("redis connection ended", {
                "error": str(exc),
            })
            REDIS_CLIENT = None
            raise TempKvNotConnected

        xor_key = None
        values_pairs = []
        for v in values_inner:
            if xor_key is None:
                xor_key = v
            else:
                values_pairs.append((xor_key, v))
                xor_key = None

        values = []
        for (key_pair, (xor_key, value)) in zip(key_pairs, values_pairs):
            if xor_key is None or value is None:
                values.append(None)
                continue

            xor_key = skein.threefish(XOR_KEY_ENC, key_pair[16:]).decrypt_block(xor_key)
            values.append(xor_value(xor_key, value))

        return values

    def get(self, key):
        return self.mget(key)[0]


def tempkv_client():
    global REDIS_CLIENT

    if REDIS_CLIENT is None:
        try:
            REDIS_CLIENT = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        except Exception as exc:
            logger.error("couldn't connect to redis", {
                "error": str(exc),
                "redis.host": REDIS_HOST,
                "redis.port": REDIS_PORT,
            })
        else:
            logger.info("new redis client", {
                "redis.host": REDIS_HOST,
                "redis.port": REDIS_PORT,
            })


    if REDIS_CLIENT:
        return TempKvClient(REDIS_CLIENT)

    raise TempKvNotConnected
        

def xor_value(key, value):
    value = bytearray(value)
    for n, byte in enumerate(value):
        value[n] ^= key[n % XOR_KEY_LEN]

    return bytes(value)
