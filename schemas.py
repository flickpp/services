
from framework.doolally import Schema, String, Number


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
