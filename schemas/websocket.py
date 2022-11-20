#!/usr/bin/env python
# -*- coding: utf-8 -*-


from lib.doolally import (
    Schema,
    StaticTypeArray,
    String,
    SchemaLessObject,
)
from schemas import (
    SESSION_ID,
    LOGIN_ID,
    USER_ID,
    TRACE_ID,
    PARENT_ID,
)
from schemas.validators import email_addr_val


WEBSOCKET_MSG_TYPES = {
    "email.message",
    "tuliptheclown.contact",
}


class WebSocketReq(Schema):
    jsonschema_description = "request to send to websocket service"

    session_ids = StaticTypeArray(required=True, element_field=SESSION_ID())
    user_ids = StaticTypeArray(required=True, element_field=USER_ID())
    login_ids = StaticTypeArray(required=True, element_field=LOGIN_ID())
    message = String(required=True, min_length=1)


def websocket_type_val(ctx_err, value):
    if value not in WEBSOCKET_MSG_TYPES:
        raise ctx_err(f"unknown websocket message type {value}")


class WebSocketMessage(Schema):
    jsonschema_description = "the message to be delivered over the websocket"

    type = String(min_length=3, required=True, validator=websocket_type_val)
    trace_id = TRACE_ID(required=True)
    parent_id = PARENT_ID(required=True)
    message = SchemaLessObject(required=True)


class EmailSentReq(Schema):
    jsonschema_description = "an email has been sent succesfully"

    email_addr = String(required=True, validator=email_addr_val)
    message = String(required=True)

