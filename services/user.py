#!/usr/bin/env python
# -*- coding: utf-8 -*-

from plantpot import Plantpot
from schemas.user import SessionResp


app = Plantpot('user')


@app.json(
    path='/session',
    require_session_id=True,
    pass_query=True,
    resp_schema=SessionResp,
)
def session(session_id, **query):
    payload = {
        "sessionId": session_id,
        "userId": None,
        "loginId": None,
    }

    if query.get('login_id'):
        payload['loginId'] = query['login_id'][0]

    if query.get('user_id'):
        payload['userId'] = query['user_id'][0]

    return payload
