
from schemas import Schema, hexstring_of_length, union_with_null


class UserResp(Schema):
    jsonschema_description = "ids of current session"

    session_id = hexstring_of_length(32, required=True)
    user_id = union_with_null(required=True,
                              element_fields=[hexstring_of_length(32)])
    login_id = union_with_null(required=True,
                              element_fields=[hexstring_of_length(32)])
