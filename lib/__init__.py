

from .tokens import build_login_token, parse_login_token


HEXCHARS = set("0123456789abcdef")


def xor_encrypt(xor_key, data):
    data = bytearray(data)
    for n, _ in enumerate(data):
        data[n] ^= xor_key[n % len(xor_key)]

    return bytes(data)


def is_hexstring(string):
    if len(string) % 2 != 0:
        return False

    for c in string.lower():
        if c not in HEXCHARS:
            return False

    return True


def traceparent(ctx):
    return f"00-{ctx.trace_id}-{ctx.span_id}-00"
