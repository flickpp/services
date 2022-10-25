import os
from time import time
from hashlib import sha256

from casket import logger

from framework import app, post_json_endpoint, EmptyResponse, get_json_endpoint
from schemas import ContactByEmailReq, ContactByNumberReq, ContactQueryResp
from clients import kvstore_insert, kvstore_retrieve

from tuliptheclown.model import Message, Contact


THROTTLE_TIMEOUT = int(os.environ.get("PLANTPOT_TULIPTHECLOWN_MESSAGE_TIMEOUT", 7200))


def contact_by_email(ctx, session_id, body, **params):
    for val in kvstore_retrieve(ctx, session_id, body['email']):
        if val.value is not None:
            return EmptyResponse("406 Already Created", [])

    logger.info("new contact", {
        "gdpr.email": body['email'],
        "gdpr.name": body['name'],
        "session_id": session_id,
    })

    contact_id = compute_contact_id(body['email'])

    # Save the contact details if they don't exist
    ins = insert(contact_id=contact_id, contact_type="email", phone_or_email=body['email'])
    ins.on_conflict_ignore().execute()

    # Save the message
    Message.create(contact_id=contact_id, name=body['name'], message=body['message'])

    if kvstore_insert(ctx, {session_id: b"1", body['email']: b"2"}, THROTTLE_TIMEOUT) != 2:
        logger.warn("couldn't insert session_id and email into k/v store - there is no throttle", {
            "session_id" : session_id,
            "gdpr.email": body['email'],
        })

    return EmptyResponse("202 Accepted", [])


def contact_by_phone(ctx, session_id, body, **params):
    for val in kvstore_retrieve(ctx, session_id, body['number']):
        if val.value is not None:
            return EmptyResponse("406 Already Created", [])

    logger.info("new contact", {
        "gdpr.phone": body['number'],
        "gdpr.name": body['name'],
        "session_id": session_id,
    })

    contact_id = compute_contact_id(body['number'])

    # Save the contact details if they don't exist
    ins = Contact.insert(contact_id=contact_id, contact_type="phone", phone_or_email=body['number'])
    ins.on_conflict_ignore().execute()

    # Save the message
    Message.create(contact_id=contact_id, name=body['name'], message=body['message'])

    if kvstore_insert(ctx, {session_id: b"1", body['number']: b"2"}, THROTTLE_TIMEOUT) != 2:
        logger.warn("couldn't insert session_id/number into kv store - there is no throttle", {
            "session_id": session_id,
            "gdpr.phone": body['number'],
        })

    return EmptyResponse("202 Accepted", [])


def contact_query(ctx, session_id, **params):
    val = kvstore_retrieve(ctx, session_id)[0]

    if val.expiry_time is None:
        time_remaining = 0
    else:
        time_remaining = val.expiry_time - int(time())
        time_remaining = max(0, val.expiry_time)

    return {
        "timeRemaining": time_remaining,
    }


def compute_contact_id(phone_or_email):
    return sha256(bytes(phone_or_email, encoding='utf8')).digest()[:16].hex()


post_json_endpoint("/contact/byemail", ContactByEmailReq, contact_by_email)
post_json_endpoint("/contact/byphone", ContactByNumberReq, contact_by_phone)
get_json_endpoint("/contact", ContactQueryResp, contact_query)
