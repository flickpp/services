
from doolally import Schema, String


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
