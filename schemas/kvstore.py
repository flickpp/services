#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lib.doolally import (
    Schema,
    union_with_null,
    StaticTypeArray,
    Number,
    String,
)
from schemas import hexstring_of_length

KEY = hexstring_of_length(32)
XOR_KEY = hexstring_of_length(64)


class KVElementReq(Schema):
    jsonschema_description = "a single element in the k/v store"

    key = KEY(required=True, description="key to insert")
    value = String(required=True,
                   min_length=1,
                   description="value to be stored with key")
    xor_key = XOR_KEY(
        required=True,
        description="key used to encrypt value, itself encrypted")
    expiry_time = Number(required=True,
                         is_int=True,
                         signed=False,
                         description="expiry time in unix time")


class KVElementResp(Schema):
    jsonschema_description = "an element in the k/v store which may or may not exist"

    key = KEY(required=True, description="key to insert")
    value = union_with_null(required=True,
                            element_fields=[
                                String(
                                    min_length=1,
                                    description="value to be stored with key")
                            ])

    xor_key = union_with_null(
        required=True,
        element_fields=[
            XOR_KEY(description="key used to encrypt value, itself encrypted")
        ])

    expiry_time = union_with_null(
        required=True,
        element_fields=[
            Number(is_int=True,
                   signed=False,
                   description="expiry time in unix time")
        ])



class InsertKVValuesReq(Schema):
    jsonschema_description = "insert array into k/v store"

    values = StaticTypeArray(required=True,
                             min_length=1,
                             element_field=KVElementReq(),
                             description="elements to insert into k/v store")


class RetrieveKVValuesResp(Schema):
    jsonschema_description = "retrieve array of values from k/v store"

    values = StaticTypeArray(required=True,
                             min_length=1,
                             element_field=KVElementResp(),
                             description="received elements from k/v store")

