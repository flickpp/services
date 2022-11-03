
from framework import get_json_endpoint, app
from lib.jsonvalidator import JSONValidator

from user.schemas import UserResp


def user(session_id, **params):
    return {
        "sessionId": session_id,
        "userId": params.get("user_id"),
        "loginId": params.get("login_id"),
    }


get_json_endpoint("/session", JSONValidator(UserResp), user)
        
