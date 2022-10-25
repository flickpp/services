
from lib.doolally import (
    Schema,
    String,
    Number,
    StaticTypeArray,
    union_with_null,
    ValidationValueError,
)


def is_hexstring(value):
    for c in value.lower():
        if c not in "0123456789abcdef":
            return False

    return True


def is_hexstring_val(ctx_err, value):
    if not is_hexstring(value):
        raise ValidationValueError("expected hexstring")


def hexstring_of_length(length, required=False, description=""):
    return String(required=required,
                  min_length=length,
                  max_length=length,
                  description=description,
                  validator=is_hexstring_val)


class KVElementReq(Schema):
    jsonschema_description = "a single element in the k/v store"

    key = hexstring_of_length(32, required=True)
    value = String(required=True, min_length=1, description="value to be stored already xor'd")
    xor_key = hexstring_of_length(64, required=True, description="key used to encrypt value, itself encrypted")
    expiry_time = Number(required=True, is_int=True, signed=False, description="expiry time in unix_time")


class KVElementResp(Schema):
    jsonschema_description = "a single element in the k/v store"

    key = hexstring_of_length(32, required=True)
    value = union_with_null(required=True,
                            element_fields=[
                                String(min_length=1, description="value to be stored already xor'd"),
                            ],
    )
    xor_key = union_with_null(
        required=True,
        element_fields=[
            hexstring_of_length(64, description="key used to encrypt value, itself encrypted"),
        ],
    )
    expiry_time = union_with_null(
        required=True, element_fields=[
            Number(is_int=True, signed=False, description="expiry time in unix_time"),
        ],
    )


class InsertKVValuesReq(Schema):
    jsonschema_description = "insert array into k/v store"

    values = StaticTypeArray(required=True,
                             min_length=1,
                             element_field=KVElementReq(),
                             description="elements to insert into the k/v store")


class RetrieveKVValuesResp(Schema):
    jsonschema_description = "retrieve array of values from k/v store"

    values = StaticTypeArray(required=True,
                             min_length=1,
                             element_field=KVElementResp(),
                             description="retrieved elements from k/v store")


class ContactByEmailReq(Schema):
    jsonschema_description = "contact by email request payload"

    name = String(required=True, description="self identifying name of person", min_length=2)
    email = String(required=True, description="self described email of person")
    message = String(required=True, description="message from person", min_length=2, max_length=2048)


class ContactByNumberReq(Schema):
    jsonschema_description = "contact by number request payload"

    name = String(required=True, description="self identifying name of person", min_length=2)
    number = String(required=True, description="self described number of person")
    message = String(required=True, description="message from person", min_length=2, max_length=2048)


class ContactQueryResp(Schema):
    jsonschema_description = "contact query to see if session_id has been used"

    time_remaining = Number(required=True,
                            description="time remaining in seconds before another request can be sent",
                            signed=False)
