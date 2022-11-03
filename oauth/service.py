import os
from urllib.parse import urlparse, urlunparse, ParseResult as URL

from framework import (
    app,
    post_json_endpoint,
    get_json_endpoint,
    get_endpoint,
    bad_request,
    EmptyResponse,
    ErrorResponse,
    Redirect,
)
from clients import kvstore_insert, kvstore_retrieve, sha256_monstermac
from lib.jsonvalidator import JSONValidator
from lib.tokens import build_login_token
from schemas import LoginData

from oauth.schemas import NewLoginReq

URL_TIMEOUT = int(os.environ.get("PLANTPOT_OAUTH_URL_TIMEOUT", "120"))
LOGIN_TOKEN_SALT_PATH = os.environ.get("PLANTPOT_LOGIN_TOKEN_SALT_PATH", "/run/secrets/logintokensalt")
LOGIN_TOKEN_SALT = open(LOGIN_TOKEN_SALT_PATH, 'rb').read()


def new_login(ctx, session_id, body, **params):
    try:
        url = urlparse(body['currentUrl'])
        assert url.scheme, "missing scheme in url"
        assert url.netloc, "mising domain"
    except Exception as exc:
        raise bad_request("Invalid URL", f"invalid current url given - {exc}")

    # insert the URL into KV store
    if kvstore_insert(ctx, {session_id: body['currentUrl']}, URL_TIMEOUT) == 1:
        return EmptyResponse("202 Created", [])
    else:
        raise ErrorResponse("500 No KV Store", "failed to insert url into kv store")


def complete_login(ctx, session_id, **params):
    url, login_tk = build_login_data(ctx, session_id)
    if url.query:
        query = url.query + b'&login_tk=' + login_tk
    else:
        query = b'login_tk=' + login_tk

    url = URL(url.scheme, url.netloc, url.path, url.params, query, url.fragment)
    raise Redirect("303 See Other", str(urlunparse(url), encoding='utf8'))


def login_data(ctx, session_id, **params):
    url, login_tk = build_login_data(ctx, session_id)
    return {
        "loginToken": str(login_tk, encoding='utf8'),
        "currentUrl": str(urlunparse(url), encoding='utf8')
    }


def build_login_data(ctx, session_id):
    url = kvstore_retrieve(ctx, session_id)[0]
    if url.value is None:
        raise bad_request("Invalid Session Id", "session id not found in oauth login")

    oauth_id = os.urandom(16)
    login_id = sha256_monstermac(oauth_id)[:16]
    return urlparse(url.value), build_login_token(LOGIN_TOKEN_SALT, login_id)


post_json_endpoint("/login",
                   JSONValidator(NewLoginReq),
                   new_login,
                   pass_context=True)

get_json_endpoint("/loginData",
                  JSONValidator(LoginData),
                  login_data,
                  pass_context=True)


get_endpoint("/login", complete_login, pass_context=True)
