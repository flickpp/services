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

EXTENSIONS = {
    "jpg": "image/jpeg",
    "txt": "text/plain",
}

CONTENT_TYPES = {v: k for k, v in EXTENSIONS.items()}


def parse_login_token(tk):
    tk = urlsafe_b64decode(tk)

    if tk[0] != 0:
        raise TokenError("login token has unrecognised version")

    if len(tk) != 57:
        raise TokenError("login token wrong length")

    expiry_time = struct.unpack(">Q", tk[9:17])[0]
    login_id = tk[17:33].hex()

    return LoginToken(login_id, expiry_time)


def build_blob_token(blob_id, extension, key):
    if isinstance(blob_id, str):
        blob_id = bytes.fromhex(blob_id)

    if not isinstance(blob_id, bytes):
        raise TypeError("blob_id must be of type bytes or a hexstring")

    if len(blob_id) != 24:
        raise ValueError("blob_id must be of length 24 bytes")

    if extension not in EXTENSIONS:
        raise TokenError(f"invalid extension {extension}")

    mac = hmac.new(key, blob_id, digestmod=sha256).digest()[:16]
    tk = urlsafe_b64encode(blob_id + mac)
    return str(tk, encoding='utf8') + '.' + extension


def read_blob_token(tk, key):
    parts = tk.split('.')
    if len(parts) != 2:
        raise TokenError("expected blob token to have exactly one .")

    tk, extension = parts[0], parts[1]
    content_type = EXTENSIONS.get(extension)
    if not content_type:
        raise TokenError(f"unrecognised file extension {extension}")

    try:
        tk = urlsafe_b64decode(tk)
    except Exception as exc:
        raise TokenError("token is not url base 64 encoded")

    if len(tk) != 40:
        raise TokenError("blob token is not of length 40")

    blob_id, mac = tk[:24], tk[24:]
    if mac != hmac.new(key, blob_id, digestmod=sha256).digest()[:16]:
        raise TokenError("invalid token digest")

    return blob_id, content_type


def compute_mac(salt, data):
    return md5(hmac.new(salt, data, digestmod=sha256).digest()).digest()
