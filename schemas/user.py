#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lib.doolally import Schema, union_with_null
from schemas import SESSION_ID, USER_ID, LOGIN_ID


class SessionResp(Schema):
    jsonschema_description = "ids of current session"

    session_id = SESSION_ID(required=True)
    user_id = union_with_null(required=True, element_fields=[USER_ID()])
    login_id = union_with_null(required=True, element_fields=[LOGIN_ID()])
