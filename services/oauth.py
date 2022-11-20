#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from urllib.parse import urlparse, urlunparse, ParseResult as URL

from casket import logger

from plantpot import Plantpot, bad_request, Redirect
from clients.kvstore import (
    insert as kv_insert,
    retrieve as kv_retrieve,
)
from clients.monstermac import sha256_monstermac
from schemas.oauth import NewLoginReq
from lib.tokens import build_login_token

URL_TIMEOUT = int(os.environ.get("PLANTPOT_OAUTH_URL_TIMEOUT", "120"))
LOGIN_TOKEN_SALT_PATH = os.environ.get('PLANTPOT_LOGIN_TOKEN_SALT_PATH',
                                       '/run/secrets/logintokensalt')
LOGIN_TOKEN_SALT = open(LOGIN_TOKEN_SALT_PATH, 'rb').read()

app = Plantpot('oauth')


@app.json(
    path="/login",
    methods=['POST'],
    pass_context=True,
    require_session_id=True,
    req_schema=NewLoginReq,
    resp_status="202 Created",
)
def new_login(ctx, body, session_id):
    url = urlparse(body['currentUrl'])
    kv_insert(ctx, 'oauth', {session_id: url}, URL_TIMEOUT)


@app.endpoint(
    path='/login',
    methods=['GET'],
    pass_context=True,
    require_session_id=True,
)
def login(ctx, session_id):
    url = kv_retrieve(ctx, 'oauth', session_id)[session_id].value
    if url is None:
        raise bad_request(
            "Missing Session Id",
            "no attempted oauth login for this session id found")

    login_id = sha256_monstermac(os.urandom(16))[:16]
    login_tk = build_login_token(LOGIN_TOKEN_SALT, login_id)

    if url.query:
        query = url.query + '&login_tk=' + login_tk
    else:
        query = 'login_tk=' + login_tk

    url = urlunparse(
        URL(
            url.scheme,
            url.netloc,
            url.path,
            url.params,
            query,
            url.fragment,
        ))

    return Redirect(url)
