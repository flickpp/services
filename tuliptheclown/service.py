import hmac
import os
from time import time
from hashlib import sha256, md5
from datetime import datetime
from base64 import urlsafe_b64encode, urlsafe_b64decode
from urllib.parse import urlparse, urlunparse, ParseResult as URL

from casket import logger

from peewee import IntegrityError
import mako as mk
from mako.template import Template

from framework import (
    app,
    post_json_endpoint,
    EmptyResponse,
    get_json_endpoint,
    get_html_endpoint,
    bad_request,
    access_denied,
    Redirect,
)
from schemas import (
    MessagesResp,
    ContactQueryResp,
    NewContactReq,
    NewContactResp,
    NewReviewReq,
    NewReviewResp,
    NewReviewResponseReq,
    is_email_val,
    is_phone_val,
)
from clients import (
    kvstore_insert,
    kvstore_retrieve,
    oauth_retrieve,
    ws_send_login_ids,
    rabbitmq_send_email,
)
from lib import xor_encrypt
from lib.jsonvalidator import JSONValidator
from lib.tokens import parse_login_token

from tuliptheclown.model import Message, Contact, Review, Event
from tuliptheclown.schemas import (
    EventResp,
    EventsResp,
    ReviewsResp,
    NewEventReq,
    NewEventResp,
    NewMessageReq,
)

THROTTLE_TIMEOUT = int(
    os.environ.get("PLANTPOT_TULIPTHECLOWN_MESSAGE_TIMEOUT", 7200))

EMAIL_FILE = os.environ.get("PLANTPOT_TULIPTHECLOWN_EMAIL_FILE", "/run/secrets/tulipemail")
TULIP_EMAIL = open(EMAIL_FILE).read()

LOGIN_IDS = [
    "66b15f1c1f8f7b4fa0bcce9c8408cc1c",
]

USER_TOKEN_SALT_PATH = os.environ.get("PLANTPOT_USER_TOKEN_SALT_PATH",
                                      "/run/secrets/usertokensalt")
USER_TOKEN_SALT = open(USER_TOKEN_SALT_PATH, 'rb').read()

REVIEWS_TEMPLATE = Template(filename="reviews.html")
ACCESS_DENIED = Template(filename="access_denied.html")
MESSAGE_EMAIL_TEMPLATE = open("message-email").read()


def new_message(ctx, session_id, body, **params):
    is_phone, is_email = phone_or_email(body['phoneOrEmail'])

    if is_phone:
        contact_type = "phone"
    elif is_email:
        contact_type = "email"
    else:
        raise bad_request("Invalid Contact",
                          "contact is neither valid phone nor email")

    for val in kvstore_retrieve(ctx, session_id, body['phoneOrEmail']):
        if val.value is not None:
            return EmptyResponse("406 Already Created", [])

    logger.info(
        "new contact", {
            f"gdpr.{contact_type}": body['phoneOrEmail'],
            "gdpr.name": body['name'],
            "session_id": session_id,
        })

    contact_id = compute_contact_id(body['name'], body['phoneOrEmail'])
    name = bytes(body['name'], encoding='utf8')
    xor_key = os.urandom(min(len(name), 8))
    name = xor_encrypt(xor_key, name)

    # Save the contact details if they don't exist
    ins = Contact.insert(contact_id=contact_id,
                         name_=name,
                         xor_key=xor_key,
                         contact_type=contact_type,
                         phone_or_email=body['phoneOrEmail'])
    ins.on_conflict_ignore().execute()

    # Save the message
    xor_key = os.urandom(16)
    message = bytes(body['message'], encoding='utf8')
    message = xor_encrypt(xor_key, message)
    Message.create(contact_id=contact_id, message=message, xor_key=xor_key)

    if kvstore_insert(ctx, {
            session_id: b"1",
            body['phoneOrEmail']: b"2"
    }, THROTTLE_TIMEOUT) != 2:
        logger.warn(
            f"couldn't insert session_id and {contact_type} into k/v store - there is no throttle",
            {
                "session_id": session_id,
                f"gdpr.{contact_type}": body['phoneOrEmail'],
            })

    # Notify any active logged in users
    ws_send_login_ids(LOGIN_IDS, "newMessage", body, schema=NewMessageReq)

    # Write the email to rabbit
    rabbitmq_send_email(TULIP_EMAIL, build_message_email(body))

    return EmptyResponse("202 Accepted", [])


def get_all_messages(session_id, login_id, **params):
    if login_id not in LOGIN_IDS:
        raise access_denied("login id not in whitelist")

    fields = (Message.message, Message.xor_key, Message.creation_time,
              Contact.name_, Contact.xor_key, Contact.phone_or_email,
              Contact.contact_id)

    # Get the most recent 50 messages
    messages = []
    query = Contact.select(*fields).join(Message).order_by(
        Message.creation_time.desc())
    for m in query.limit(50):
        message = str(xor_encrypt(m.message.xor_key, m.message.message),
                      encoding='utf8')
        name = str(xor_encrypt(m.xor_key, m.name_), encoding='utf8')

        messages.append({
            "name": name,
            "message": message,
            "phoneOrEmail": m.phone_or_email,
            "creationTime": m.message.creation_time.isoformat(),
            "contactId": m.contact_id.hex(),
        })

    return dict(messages=messages)


def contact_query(ctx, session_id, **params):
    val = kvstore_retrieve(ctx, session_id)[0]

    if val.expiry_time is None:
        time_remaining = 0
    else:
        time_remaining = val.expiry_time - int(time())
        time_remaining = max(0, time_remaining)

    return {
        "timeRemaining": time_remaining,
    }


def new_contact(session_id, login_id, body, **params):
    if login_id not in LOGIN_IDS:
        raise access_denied("login id not in whitelist")

    is_phone, is_email = phone_or_email(body['phoneOrEmail'])
    if is_phone:
        contact_type = "phone"
    elif is_email:
        contact_type = "email"
    else:
        raise bad_request("Invalid Contact",
                          "contact is neither phone nor email address")

    contact_id = compute_contact_id(body['name'], body['phoneOrEmail'])

    name = bytes(body['name'], encoding='utf8')
    xor_key = os.urandom(min(len(name), 8))
    name = xor_encrypt(xor_key, name)

    # Save the contact details if they don't exist
    ins = Contact.insert(contact_id=contact_id,
                         name_=name,
                         xor_key=xor_key,
                         contact_type=contact_type,
                         phone_or_email=body['phoneOrEmail'])

    ins.on_conflict_ignore().execute()

    return {
        "contactId": contact_id.hex(),
    }


def new_event(session_id, login_id, body, **params):
    contact_id = new_contact(session_id, login_id, body, **params)['contactId']

    event_id = os.urandom(16)
    contact_id = bytes.fromhex(contact_id)
    date = datetime.strptime(body['date'], "%Y-%m-%d")
    start_time = datetime.strptime(body['startTime'], "%H:%M")
    end_time = datetime.strptime(body['endTime'], "%H:%M")

    if start_time >= end_time:
        raise bad_request("Invalid Time", "end time is before start time")

    if body['deposit'] > body['totalPrice']:
        raise bad_request("Invalid Deposit",
                          "depsoit is greater than total price")

    Event.create(event_id=event_id,
                 contact_id=contact_id,
                 date_=date,
                 start_time=start_time,
                 end_time=end_time,
                 description=bytes(body['description'], encoding='utf8'),
                 total_price=body['totalPrice'],
                 deposit=body['deposit'])

    return {
        "eventId": str(urlsafe_b64encode(event_id), encoding='utf8'),
        "userToken": build_user_token(contact_id),
    }


def get_event(session_id, user_id, **params):
    try:
        event_id = params.get("event_id")
        if event_id is None or len(event_id) != 1:
            raise Exception("expected exactly one event_id in url params")

        event_id = urlsafe_b64decode(event_id[0])
        assert len(event_id) == 16, "event id must have length 16"

    except Exception as exc:
        raise bad_request("Invalid Event Id", str(exc))

    contact_id = bytes.fromhex(user_id)

    filter = (Event.contact_id == contact_id) & (Event.event_id == event_id)
    ev = list(Event.select().where(filter))
    if not ev:
        raise access_denied(
            "event id does not exist or does not belong to this user")
    ev = ev[0]

    review = None

    if ev.review_id:
        rev = list(Review.select().where(Review.review_id == ev.review_id))
        if not rev or len(rev) != 1:
            logger.error("review is registered to event but we can't find it",
                         {
                             "review_id": ev.review_id.hex(),
                         })
        else:
            rev = rev[0]
            text = str(xor_encrypt(rev.xor_key, rev.review), encoding='utf8')
            review = {
                "review": text,
                "creationTime": rev.creation_time.isoformat(),
                "response": None,
                "responseTime": None,
            }

            if rev.response:
                review['response'] = str(rev.response, encoding='utf8')

            if rev.response_time:
                review['responseTime'] = rev.response_time.isoformat()

    return {
        "date": ev.date_.strftime("%a %d %b %Y"),
        "startTime": ev.start_time.strftime("%H:%M"),
        "endTime": ev.end_time.strftime("%H:%M"),
        "description": str(ev.description, encoding='utf8'),
        "totalPrice": ev.total_price,
        "deposit": ev.deposit,
        "review": review,
    }


def get_all_events(session_id, login_id, **params):
    if login_id not in LOGIN_IDS:
        raise access_denied("login id is not in whitelist")

    events = []
    for ev in Event.select().order_by(Event.date_.desc()).limit(30):
        event_id = str(urlsafe_b64encode(ev.event_id), encoding='utf8')
        user_token = build_user_token(ev.contact_id.contact_id)

        events.append({
            "date": ev.date_.strftime("%a %d %b %Y"),
            "startTime": ev.start_time.strftime("%H:%M"),
            "endTime": ev.end_time.strftime("%H:%M"),
            "description": str(ev.description, encoding='utf8'),
            "eventId": event_id,
            "userToken": user_token,
        })

    return dict(events=events)


def new_review(session_id, user_id, body, **params):
    contact_id = bytes.fromhex(user_id)
    event_id = urlsafe_b64decode(body['eventId'])
    review = bytes(body['review'], encoding='utf8')
    review_id = sha256(review).digest()[:16]

    # Does the event id exist and belong to this user?
    query = list(
        Event.select(Event.event_id,
                     Event.contact_id).where(Event.contact_id == contact_id))
    if not query or query[0].event_id != event_id:
        raise access_denied(
            "event Id does not exist or does not belong to this user")

    xor_key = os.urandom(16)
    review = xor_encrypt(xor_key, review)

    ins = Review.insert(review_id=review_id,
                        contact_id=contact_id,
                        review=review,
                        xor_key=xor_key)
    ins.on_conflict_ignore().execute()

    Event.update({
        Event.review_id: review_id
    }).where(Event.event_id == event_id).execute()

    return {
        "reviewId": review_id.hex(),
    }


def get_all_reviews(session_id, login_id, **params):
    if login_id not in LOGIN_IDS:
        raise access_denied("login id not in allowed whitelist")

    args = (
        Review.review_id,
        Review.xor_key,
        Review.review,
        Review.weight,
    )

    reviews = {}
    for r in Review.select(*args):
        review = str(xor_encrypt(r.xor_key, r.review), encoding='utf8')

        reviews[r.review_id] = {
            "weight": r.weight,
            "reviewId": r.review_id.hex(),
            "review": review,
            "eventId": None,
            "userToken": None,
        }

    review_ids = list(reviews.keys())
    args = (Event.event_id, Event.contact_id, Event.review_id)
    for ev in Event.select(*args).where(Event.review_id.in_(review_ids)):
        event_id = str(urlsafe_b64encode(ev.review_id.review_id),
                       encoding='utf8')
        user_token = build_user_token(ev.contact_id.contact_id)

        reviews[ev.review_id.review_id]['eventId'] = event_id
        reviews[ev.review_id.review_id]['userToken'] = user_token

    return dict(reviews=list(reviews.values()))


def review_response(session_id, login_id, body, **params):
    if login_id not in LOGIN_IDS:
        raise access_denied("login id not in allowed whitelist")

    review_id = bytes.fromhex(body['reviewId'])
    data = {
        Review.weight: body['weight'],
    }
    if body['response']:
        data[Review.response] = bytes(body['response'], encoding='utf8')
        data[Review.response_time] = datetime.now()

    Review.update(data).where(Review.review_id == review_id).execute()

    return EmptyResponse("200 Ok", [])


def get_reviews(session_id, **params):
    args = (
        Review.review,
        Review.xor_key,
        Review.creation_time,
        Review.response,
        Review.weight,
        Contact.name_,
        Contact.xor_key,
    )

    reviews = []
    filter = Review.weight != 0
    order = Review.weight.desc()
    for c in Contact.select(
            *args).join(Review).where(filter).order_by(order).limit(50):
        r = c.review

        reviews.append({
            "review":
            str(xor_encrypt(r.xor_key, r.review), encoding='utf8'),
            "creationTime":
            r.creation_time.strftime("%b %Y"),
            "response":
            None,
            "name":
            str(xor_encrypt(c.xor_key, c.name_), encoding='utf8'),
        })

        if r.response:
            reviews[-1]['response'] = str(r.response, encoding='utf8')

    return REVIEWS_TEMPLATE.render(reviews=reviews)


def login(ctx, session_id, **params):
    login = oauth_retrieve(ctx, session_id)
    if login is None:
        return ACCESS_DENIED.render(
            reason="no oauth login found for this session id")

    if parse_login_token(login['loginToken']).login_id not in LOGIN_IDS:
        return ACCESS_DENIED.render(reason="login not allowed for this user")

    url = urlparse(bytes(login['currentUrl'], encoding='utf8'))
    tk = bytes(login['loginToken'], encoding='utf8')

    if url.query:
        query = url.query + b'&login_tk=' + tk
    else:
        query = b'login_tk=' + tk

    url = URL(url.scheme, url.netloc, url.path, url.params, query,
              url.fragment)
    raise Redirect("303 See Other", str(urlunparse(url), encoding='utf8'))


def build_message_email(body):
    return MESSAGE_EMAIL_TEMPLATE.format(**body)


def phone_or_email(phone_or_email):
    is_phone = True
    is_email = True

    try:
        is_email_val(ValueError, phone_or_email)
    except ValueError:
        is_email = False

    try:
        is_phone_val(ValueError, phone_or_email)
    except ValueError:
        is_phone = False

    return (is_phone, is_email)


def compute_contact_id(name, phone_or_email):
    return sha256(bytes(name + phone_or_email, encoding='utf8')).digest()[:16]


def build_user_token(user_id):
    mac = hmac.new(USER_TOKEN_SALT, msg=user_id, digestmod=sha256).digest()
    token = urlsafe_b64encode(user_id + md5(mac).digest())
    return str(token, encoding='utf8')


post_json_endpoint("/message",
                   JSONValidator(NewMessageReq),
                   new_message,
                   pass_context=True)

get_json_endpoint("/messages",
                  JSONValidator(MessagesResp),
                  get_all_messages,
                  require_login_id=True)

get_json_endpoint("/contact",
                  JSONValidator(ContactQueryResp),
                  contact_query,
                  pass_context=True)

post_json_endpoint("/contact",
                   JSONValidator(NewContactReq),
                   new_contact,
                   require_login_id=True,
                   resp_schema_sanity=JSONValidator(NewContactResp))

post_json_endpoint("/event",
                   JSONValidator(NewEventReq),
                   new_event,
                   require_login_id=True,
                   resp_schema_sanity=JSONValidator(NewEventResp))

get_json_endpoint("/event",
                  JSONValidator(EventResp),
                  get_event,
                  require_user_id=True)

get_json_endpoint("/events",
                  JSONValidator(EventsResp),
                  get_all_events,
                  require_login_id=True)

post_json_endpoint("/review",
                   JSONValidator(NewReviewReq),
                   new_review,
                   require_user_id=True,
                   resp_schema_sanity=JSONValidator(NewReviewResp))

get_json_endpoint("/review",
                  JSONValidator(ReviewsResp),
                  get_all_reviews,
                  require_login_id=True)

post_json_endpoint("/reviewResponse",
                   JSONValidator(NewReviewResponseReq),
                   review_response,
                   require_login_id=True)

get_html_endpoint("/reviews", get_reviews)

get_html_endpoint("/login", login, pass_context=True)
