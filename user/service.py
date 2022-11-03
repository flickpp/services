
from framework import get_json_endpoint, app
from lib.jsonvalidator import JSONValidator

from user.schemas import UserResp


def user(session_id, **params):
    session = {
        "sessionId": session_id,
        "userId": None,
        "loginId": None,
    }

    if params.get('login_id') and len(params['login_id']) == 1:
        session['loginId'] = params['login_id'][0]

    if params.get('user_id') and len(params['user_id']) == 1:
        session['userId'] = params['user_id'][0]

    return session


get_json_endpoint("/session", JSONValidator(UserResp), user)
        
