#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from datetime import datetime
from urllib.parse import urlparse

from lib import is_hexstring


DOMAIN_REGEX = re.compile('^[A-Za-z0-9-]')
NAME_REGEX = re.compile('^[A-Za-z0-9-\.]')


def hexstring_val(ctx_err, value):
    if not is_hexstring(value):
        raise ctx_err("expected hexstring")


def javascript_date_val(ctx_err, value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except Exception as exc:
        raise ctx_err(str(exc))


def date_val(ctx_err, value):
    try:
        datetime.strptime(value, "%d %b %Y")
    except Exception as exc:
        raise ctx_err(str(exc))


def time_val(ctx_err, value):
    try:
        datetime.strptime(value, "%H:%M")
    except Exception as exc:
        raise ctx_err(str(exc))


def email_addr_val(ctx_err, value):
    parts = value.split('@')
    if len(parts) != 2:
        raise ctx_err("expected exactly one @ in email address")

    name, domain = parts

    for d in domain.split('.'):
        if not d:
            raise ctx_err("repeated . not allowed in email domain")

        if not DOMAIN_REGEX.match(d):
            raise ctx_err("subdomain in email not valid")

    if not NAME_REGEX.match(name):
        raise ctx_err("invalid name in email address")



def phone_val(ctx_err, value):
    if not value:
        raise ctx_err("empty phone number not allowed")

    if value[0] == '+':
        value = value[1:]

    for v in map(ord, value):
        if v < ord('0') or v > ord('9'):
            raise ctx_err("invalid character in phone number")


def isotimestamp_val(ctx_err, value):
    try:
        datetime.fromisoformat(value)
    except Exception as exc:
        raise ctx_err(str(exc))


def full_url_val(ctx_err, value):
    try:
        url = urlparse(value)

        assert url.scheme.lower() == "https", "empty url scheme"
        assert url.netloc, "empty url domain"

    except Exception as exc:
        raise ctx_err(str(exc))

