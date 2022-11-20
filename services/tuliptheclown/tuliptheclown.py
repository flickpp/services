#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import datetime
from hashlib import sha256

from casket import logger

from mako.template import Template

from clients.exceptions import ClientError
from clients.kvstore import insert as kv_insert
from clients.kvstore import retrieve as kv_retrieve
from clients.rabbitmq import send_email as rabbitmq_send_email
from lib import xor_encrypt
from lib.tokens import build_user_token
from models.tuliptheclown import Contact, Event, Message, Review
from plantpot import (Plantpot, UrlParamArg, already_created, bad_request,
                      forbidden)
from schemas.tuliptheclown import (ContactQueryResp, EventResp, EventsResp,
                                   MessagesResp, NewContactReq, NewContactResp,
                                   NewEventReq, NewEventResp, NewMessageReq,
                                   NewReviewReq, NewReviewResp, ReviewsResp,
                                   NewReviewResponseReq)
from schemas.validators import email_addr_val, phone_val

app = Plantpot('tuliptheclown')

EMAIL_FILE = os.environ.get("PLANTPOT_TULIPTHECLOWN_EMAIL_FILE",
                            "/run/secrets/tulipemail")
TULIP_EMAIL = open(EMAIL_FILE).read()
THROTTLE_TIMEOUT = int(
    os.environ.get('PLANTPOT_TULIPTHECLOWN_THROTTLE_TIMEOUT', "120"))

MESSAGE_EMAIL_TEMPLATE = open('tuliptheclown/message-email').read()
REVIEWS_TEMPLATE = Template(filename="tuliptheclown/reviews.html")
ACCESS_DENIED = Template(filename="access_denied.html")

USER_TOKEN_SALT_PATH = os.environ.get("PLANTPOT_USER_TOKEN_SALT_PATH",
                                      "/run/secrets/usertokensalt")
USER_TOKEN_SALT = open(USER_TOKEN_SALT_PATH, 'rb').read()

LOGIN_IDS = [
    "66b15f1c1f8f7b4fa0bcce9c8408cc1c",
]


@app.json(
    path="/message",
    methods=['POST'],
    pass_context=True,
    req_schema=NewMessageReq,
    require_session_id=True,
    resp_status="202 Created",
)
def new_message(ctx, body, session_id):
    is_phone, is_email = phone_or_email(body['phoneOrEmail'])

    if is_phone:
        contact_type = "phone"
    elif is_email:
        contact_type = "email"
    else:
        raise bad_request("Invalid Contact",
                          "Contact is neither valid phone nor email")

    keys = (session_id, body['phoneOrEmail'])

    try:
        for val in kv_retrieve(ctx, 'tuliptheclown.contact', *keys).values():
            if val.value is not None:
                raise already_created()
    except ClientError as exc:
        logger.error("couldn't insert to kvstore - there is no throttle", {
            "error": str(exc),
        })

    contact_id = compute_contact_id(body['name'], body['phoneOrEmail'])

    # Save the contact details if they don't exist
    xor_key = os.urandom(8)
    name = xor_encrypt(xor_key, bytes(body['name'], encoding='utf8'))
    Contact.insert(
        contact_id=contact_id,
        name_=name,
        xor_key=xor_key,
        contact_type=contact_type,
        phone_or_email=body['phoneOrEmail'],
    ).on_conflict_ignore().execute()

    # Save the message
    xor_key = os.urandom(16)
    message = xor_encrypt(xor_key, bytes(body['message'], encoding='utf8'))
    Message.create(contact_id=contact_id, message=message, xor_key=xor_key)

    logger.info("new message", {
        "gdpr.name": body['name'],
        f"gdpr.{contact_type}": body['phoneOrEmail'],
    })

    # Insert into throttle
    mapping = {session_id: "1", body['phoneOrEmail']: "2"}
    try:
        kv_insert(ctx, 'tuliptheclown.contact', mapping, THROTTLE_TIMEOUT)
    except ClientError as exc:
        logger.error(
            "couldn't insert record to kvstore - there is no throttle", {
                "error": str(exc),
            })

    # send email
    try:
        rabbitmq_send_email(ctx,
                            TULIP_EMAIL,
                            build_message_email(body),
                            session_id=session_id)
    except ClientError as exc:
        logger.error("couldn't send msg to rabbitmq - there is no email", {
            "error": str(exc),
        })


@app.json(
    path="/messages",
    methods=['GET'],
    require_login_id=True,
    resp_schema=MessagesResp,
)
def all_messages(login_id):
    if login_id not in LOGIN_IDS:
        raise forbidden("login id not valid")

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


@app.json(
    path="/contact",
    methods=['GET'],
    pass_context=True,
    require_session_id=True,
    resp_schema=ContactQueryResp,
)
def contact_query(ctx, session_id):
    val = kv_retrieve(ctx, 'tuliptheclown.contact', session_id)[session_id]

    time_remaining = val.ttl or 0

    return {
        "timeRemaining": time_remaining,
    }


@app.json(
    path="/contact",
    methods=['POST'],
    require_login_id=True,
    req_schema=NewContactReq,
    resp_status="202 Created",
    resp_schema=NewContactResp,
)
def new_contact(body, login_id):
    if login_id not in LOGIN_IDS:
        raise forbidden("login id not valid")

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
    xor_key = os.urandom(8)
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


@app.json(
    path="/event",
    methods=['POST'],
    require_login_id=True,
    req_schema=NewEventReq,
    resp_schema=NewEventResp,
    resp_status="202 Created",
)
def new_event(body, login_id):
    if login_id not in LOGIN_IDS:
        raise forbidden("login id not valid")

    contact_id = new_contact(body, login_id)['contactId']

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
        "userToken": build_user_token(USER_TOKEN_SALT, contact_id),
    }


def event_id_sanity(err, event_id):
    try:
        event_id = urlsafe_b64decode(event_id)

        if len(event_id) != 16:
            raise Exception("expected 16 bytes encoded")

    except Exception as exc:
        raise err(f"invalid event_id url param {exc}")


@app.json(
    path="/event",
    require_user_id=True,
    param_args=[UrlParamArg("event_id", event_id_sanity)],
    resp_schema=EventResp,
)
def get_event(user_id, event_id):
    contact_id = bytes.fromhex(user_id)
    event_id = urlsafe_b64decode(event_id)

    filter = (Event.contact_id == contact_id) & (Event.event_id == event_id)
    ev = list(Event.select().where(filter))
    if not ev:
        raise forbidden(
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


@app.json(
    path="/events",
    require_login_id=True,
    resp_schema=EventsResp,
)
def get_all_events(login_id):
    if login_id not in LOGIN_IDS:
        raise forbidden("login id not valid")

    events = []
    for ev in Event.select().order_by(Event.date_.desc()).limit(30):
        event_id = str(urlsafe_b64encode(ev.event_id), encoding='utf8')
        user_token = build_user_token(USER_TOKEN_SALT,
                                      ev.contact_id.contact_id)

        events.append({
            "date": ev.date_.strftime("%a %d %b %Y"),
            "startTime": ev.start_time.strftime("%H:%M"),
            "endTime": ev.end_time.strftime("%H:%M"),
            "description": str(ev.description, encoding='utf8'),
            "eventId": event_id,
            "userToken": user_token,
        })

    return dict(events=events)


@app.json(
    path="/review",
    methods=['POST'],
    require_user_id=True,
    req_schema=NewReviewReq,
    resp_schema=NewReviewResp,
    resp_status="202 Created",
)
def new_review(body, user_id):
    contact_id = bytes.fromhex(user_id)
    event_id = urlsafe_b64decode(body['eventId'])
    review = bytes(body['review'], encoding='utf8')
    review_id = sha256(review).digest()[:16]

    # Does the event id exist and belong to this user?
    filter = (Event.contact_id == contact_id) & (Event.event_id == event_id)
    ev = list(Event.select().where(filter))
    if not ev:
        raise forbidden(
            "event id does not exist or does not belong to this user")

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


@app.json(
    path="/review",
    methods=['GET'],
    require_login_id=True,
    resp_schema=ReviewsResp,
)
def get_all_reviews(login_id):
    if login_id not in LOGIN_IDS:
        raise forbidden("login id not valid")

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
        user_token = build_user_token(USER_TOKEN_SALT, ev.contact_id.contact_id)

        reviews[ev.review_id.review_id]['eventId'] = event_id
        reviews[ev.review_id.review_id]['userToken'] = user_token

    return dict(reviews=list(reviews.values()))

@app.json(
    path='/review-response',
    methods=['POST'],
    require_login_id=True,
    req_schema=NewReviewResponseReq,
)
def review_response(body, login_id):
    if login_id not in LOGIN_IDS:
        raise forbidden("login id not valid")

    review_id = bytes.fromhex(body['reviewId'])
    data = {
        Review.weight: body['weight'],
    }
    if body['response']:
        data[Review.response] = bytes(body['response'], encoding='utf8')
        data[Review.response_time] = datetime.now()

    Review.update(data).where(Review.review_id == review_id).execute()


@app.html(
    path="/reviews",
)
def get_reviews():
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


@app.html(
    path="/login",
    pass_context=True,
)
def login(ctx):
    return ACCESS_DENIED.render("login not allowed for this user")


def phone_or_email(value):
    is_phone = True
    is_email = True

    try:
        email_addr_val(ValueError, value)
    except ValueError:
        is_email = False

    try:
        phone_val(ValueError, value)
    except ValueError:
        is_phone = False

    return is_phone, is_email


def compute_contact_id(name, phone_or_email):
    return sha256(bytes(name + phone_or_email, encoding='utf8')).digest()[:16]


def build_message_email(body):
    return MESSAGE_EMAIL_TEMPLATE.format(**body)
