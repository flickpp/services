import struct
import hmac
from collections import namedtuple
from hashlib import sha256, md5
from os import urandom, environ
from time import time
from base64 import urlsafe_b64encode, urlsafe_b64decode

# Set expiry time to 2 minutes
EXPIRY_TIME = 60 * 2

class TokenError(Exception):
    pass


def build_login_token(salt, login_id):
    expiry_time = int(time()) + EXPIRY_TIME
    expiry_time = struct.pack(">Q", expiry_time)
    flags = b'\x00' * 8

    tk = b'\x00' + urandom(8) + expiry_time + login_id + flags
    return urlsafe_b64encode(tk + compute_mac(salt, tk))


LoginToken = namedtuple("LoginToken", ("login_id", "expiry_time"))


def parse_login_token(tk):
    tk = urlsafe_b64decode(tk)

    if tk[0] != 0:
        raise TokenError("login token has unrecognised version")

    if len(tk) != 57:
        raise TokenError("login token wrong length")

    expiry_time = struct.unpack(">Q", tk[9:17])[0]
    login_id = tk[17:33].hex()

    return LoginToken(login_id, expiry_time)


def compute_mac(salt, data):
    return md5(hmac.new(salt, data, digestmod=sha256).digest()).digest()

