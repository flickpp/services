#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import partial

from lib.doolally import String
from schemas.validators import hexstring_val


def hexstring_of_length(length):
    return partial(String,
                   min_length=length,
                   max_length=length,
                   validator=hexstring_val)


SESSION_ID = hexstring_of_length(32)
USER_ID = hexstring_of_length(32)
LOGIN_ID = hexstring_of_length(32)
TRACE_ID = hexstring_of_length(32)
PARENT_ID = hexstring_of_length(16)
