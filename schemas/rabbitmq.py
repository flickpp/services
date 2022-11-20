#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lib.doolally import (
    Schema,
    String,
    SchemaLessObject,
    union_with_null,
)
from schemas import TRACE_ID, PARENT_ID, SESSION_ID
from schemas.validators import email_addr_val

RABBIT_MSG_TYPES = {
    "email",
}


def msg_type_val(ctx_err, value):
    if value not in RABBIT_MSG_TYPES:
        raise ctx_err(f"unrecognised rabbit msg type {value}")


class RabbitMessage(Schema):
    trace_id = TRACE_ID(required=True)
    parent_id = PARENT_ID(required=True)
    type = String(required=True, validator=msg_type_val)
    payload = SchemaLessObject(required=True)


class EmailMessage(Schema):
    jsonschema_description = "email payload for rabbit"

    email_addr = String(required=True, validator=email_addr_val)
    message = String(required=True, min_length=1)
    session_id = union_with_null(required=True, element_fields=[SESSION_ID()])
