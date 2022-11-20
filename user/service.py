import os
from hashlib import sha512

from framework import (
    get_json_endpoint,
    app,
    EmptyResponse,
    post_json_endpoint,
    access_denied,
    Endpoint,
    add_endpoint,
    login_id_sanity,
)
from plantpot import Plantpot
from lib.jsonvalidator import JSONValidator
from lib.tokens import append_login_token, build_login_token
from clients import sha256_monstermac, rabbitmq_send_email

from user.schemas import UserResp
from user.model import EmailLogin, Login

NEW_ACCOUNT_EMAIL_PATH = os.environ.get("PLANTPOT_USER_NEW_ACCOUNT_EMAIL",
                                        "newaccountemail")
NEW_ACCOUNT_EMAIL = open(NEW_ACCOUNT_EMAIL_PATH).read()

LOGIN_TOKEN_SALT_PATH = os.environ.get("PLANTPOT_LOGIN_TOKEN_SALT_PATH",
                                       "/run/secrets/logintokensalt")
LOGIN_TOKEN_SALT = open(LOGIN_TOKEN_SALT_PATH, 'rb').read()


app = Plantpot('user')


@app.json(
    path="/session",
    require_session_id=True,
    pass_query=True,
    resp_schema=SessionResp,
)
def session(session_id, **query):
    session = {
        "sessionId": session_id,
        "userId": None,
        "loginId": None,
    }

    if query.get('login_id') and len(query['login_id']) == 1:
        session['loginId'] = query['login_id'][0]

    if query.get('user_id') and len(query['user_id']) == 1:
        session['userId'] = query['user_id'][0]

    return session


def match_update_login_flags(req):
    req.path() == "/loginFlags" and req.method() == "PUT"


def update_login_flags(login_id, login_flags, **params):
    login_flags = login_flags.split(',')
    login_id = bytes.fromhex(login_id)

    Login.update({
        "login_flags": login_flags
    }).where(Login.login_id == login_id)

    return EmptyResponse("200 Ok", [])


@app.json(
    path="/email-login/create",
    req_schema=EmailLoginCreateReq,
    resp_status="202 Created",
)
def email_login_create(body):
    pass


def create_email_account(email):
    mac = sha256_monstermac(email)
    login_id, upper_salt = mac[:16], mac[16:]

    if list(
            EmailLogin.select(
                EmailLogin.login_id).where(EmailLogin.login_id == login_id)):
        # Already exists
        return

    ins = EmailLogin.insert({
        "email": email,
        "login_id": login_id,
        "lower_salt": b'\x00' * 16,
        "upper_salt": upper_salt,
        "login_attempt_salt": b'\x00' * 32,
        "inner_value": b'\x00' * 32,
    })

    ins.execute()

    return login_id


def build_new_account_email(login_id, url):
    url = append_login_token(url, LOGIN_TOKEN_SALT, login_id)
    return NEW_ACCOUNT_EMAIL.format(url=urlunparse(url))


def new_email_login(session_id, body, **params):
    login_id = create_email_account(body['email'])
    if login_id is None:
        return EmptyResponse("202 Created", [])

    url = urlparse(body['url'])

    # Send an email with a link including login token
    rabbitmq_send_email(body['email'], build_new_account_email(login_id, url))

    return EmptyResponse("202 Created", [])


def new_password(login_id, body, **params):
    lower_salt = os.urandom(16)

    login_id = bytes.fromhex(login_id)
    EmailLogin.update({
        "lower_salt": lower_salt
    }).where(EmailLogin.login_id == login_id)

    rec = EmailLogin.select(
        (EmailLogin.upper_salt,
         EmailLogin.login_id)).where(EmailLogin.login_id == login_id).one()

    return {
        "loginId": login_id.hex(),
        "lowerSalt": lower_salt.hex(),
        "upperSalt": rec.upper_salt.hex(),
    }


def set_password(login_id, body, **params):
    EmailLogin.update({"inner_value": bytes.fromhex(body['innerValue'])})
    return EmptyResponse("200 Ok", [])


def login_new_device(body, **params):
    mac = sha256_monstermac(body['email'])
    login_id = mac[:16]
    upper_salt = mac[16:]

    args = (
        EmailLogin.login_id,
        EmailLogin.lower_salt,
        EmailLogin.upper_salt,
    )
    recs = list(EmailLogin.select(args).where(EmailLogin.login_id == login_id))

    if not recs:
        # email doesn't exist - don't leak this fact
        # to anybody probing the endpoint.
        return {
            "loginId": login_id.hex(),
            "upperSalt": upper_salt.hex(),
            "lowerSalt": os.urandom(16).hex(),
        }

    rec = recs[0]

    return {
        "loginId": login_id.hex(),
        "lowerSalt": rec.lower_salt.hex(),
        "upperSalt": rec.upper_salt.hex(),
    }


def new_login(session_id, body, **params):
    login_id = bytes.fromhex(body['loginId'])
    login_attempt_salt = os.urandom(32)

    EmailLogin.update({
        "login_attempt_salt": login_attempt_salt
    }).where(EmailLogin.login_id == login_id)

    return {
        "loginId": login_id.hex(),
        "loginAttemptSalt": login_attempt_salt.hex(),
    }


def login(session_id, body, **params):
    login_id = bytes.fromhex(body['loginId'])
    login_attempt_password = bytes.fromhex(body['loginAttemptPassword'])

    args = (
        EmailLogin.login_id,
        EmailLogin.inner_value,
        EmailLogin.login_attempt_salt,
    )
    recs = list(EmailLogin.select(args).where(EmailLogin.login_id == login_id))

    if not recs:
        # login_id doesn't exist
        raise access_denied("invalid password")

    rec = recs[0]

    if sha512(rec.login_attempt_salt +
              rec.inner_value).digest() == login_attempt_password:
        # success
        login_tk = build_login_token(LOGIN_TOKEN_SALT, login_id)
        return {
            "loginTk": str(login_tk, encoding='utf8'),
        }

    raise access_denied("invalid password")


def login_flags_sanity(err, flags):
    for f in flags.split(','):
        if f not in LOGIN_FLAGS:
            raise err(f"invalid login flag {f}")


get_json_endpoint("/session", JSONValidator(UserResp), session)


UPDATE_LOGIN_FLAGS = Endpoint(update_login_flags, match_update_login_flags)
UPDATE_LOGIN_FLAGS.add_url_param_arg('login_id', sanity=login_id_sanity)
UPDATE_LOGIN_FLAGS.add_url_param_arg('login_flags', sanity=login_flags_sanity)

add_endpoint(UPDATE_LOGIN_FLAGS)

