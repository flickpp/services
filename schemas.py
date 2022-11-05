from datetime import datetime

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
        raise ctx_err("expected hexstring")


def javascript_date_val(ctx_err, value):
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except Exception as exc:
        raise ctx_err(str(exc))

def is_date_val(ctx_err, value):
    try:
        datetime.strptime(value, "%d %b %Y")
    except Exception as exc:
        raise ctx_err(str(exc))


def is_time_val(ctx_err, value):
    try:
        datetime.strptime(value, "%H:%M")
    except Exception as exc:
        raise ctx_err(str(exc))


def is_email_val(ctx_err, value):
    at_count = 0
    for v in value.lower():
        if v == '@':
            at_count += 1
            continue

        if v == '.':
            continue

        if v not in "abcdefghijklmnopqrstuvwxyz-_":
            raise ctx_err(f"char not valid in email {v}")

    if at_count != 1:
        raise ctx_err("expected exactly one @")


def is_phone_val(ctx_err, value):
    if not value:
        raise ctx_err("phone number empty")

    if value[0] == "+":
        value = value[1:]

    for v in value:
        v = ord(v)

        if v < ord('0') or v > ord('9'):
            raise ctx_err("invalid character in phone number")


def is_isotimestamp_val(ctx_err, value):
    try:
        datetime.fromisoformat(value)
    except Exception as exc:
        raise ctx_err(str(exc))
        


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


class NewMessageReq(Schema):
    jsonschema_description = "contact by number request payload"

    name = String(required=True, description="self identifying name of person", min_length=2, max_length=32)
    phone_or_email = String(required=True, description="self described phone or email of person")
    message = String(required=True, description="message from person", min_length=2, max_length=4096)


class Message(Schema):
    jsonschema_description = "an individual message stored on the server"

    name = String(required=True, description="self identifying name of person", min_length=2, max_length=32)
    phone_or_email = String(required=True, description="self described phone or email of person")
    contact_id = hexstring_of_length(32, required=True, description="contact id of individual")
    message = String(required=True, description="message from person", min_length=2, max_length=4096)
    creation_time = String(required=True,
                           description="timestamp message was created",
                           validator=is_isotimestamp_val)


class MessagesResp(Schema):
    jsonschema_description = "array of messages received by server"

    messages = StaticTypeArray(
        required=True,
        element_field=Message(),
        description="an individual message")


class ContactQueryResp(Schema):
    jsonschema_description = "contact query to see if session_id has been used"

    time_remaining = Number(required=True,
                            description="time remaining in seconds before another request can be sent",
                            signed=False)


def is_contact_type_val(ctx_err, value):
    if value == "email" or value == "phone":
        return

    raise ctx_err(f"bad contact_type value {value}")


class NewContactReq(Schema):
    jsonschema_description = "create a new contact in DB"

    name = String(required=True, description="name of person", min_length=4, max_length=64)
    phoneOrEmail = String(required=True, description="contact string")


class NewContactResp(Schema):
    jsonschema_description = "create a new contact response - contains contact_id"

    contact_id = hexstring_of_length(32, required=True, description="contact_id of created contact")


class NewReviewReq(Schema):
    jsonschema_description = "new review"

    review = String(required=True, min_length=1, max_length=4096, description="review to be posted")
    event_id = String(required=True, min_length=16, description="event to which review is attached")


class NewReviewResp(Schema):
    jsonschema_description = "respond to new review with review id"

    review_id = hexstring_of_length(32, required=True, description="review id")


class NewReviewResponseReq(Schema):
    jsonschema_description = "respond to an exisitng review"

    review_id = hexstring_of_length(32, required=True, description="review id")
    weight = Number(required=True, is_int=True, min_value=0, max_value=255, description="weight")
    response = union_with_null(required=True,
                               element_fields=[
                                   String(max_length=4096, description="tulip response to comment"),
                               ]
               )


class LoginData(Schema):
    jsonschema_description = "login data for current session"

    current_url = String(required=True, min_length=10, description="url when browser started login")
    login_token = String(required=True, description="login token for client")
