

from .tokens import build_login_token, parse_login_token


def xor_encrypt(xor_key, data):
    data = bytearray(data)
    for n, _ in enumerate(data):
        data[n] ^= xor_key[n % len(xor_key)]

    return bytes(data)
