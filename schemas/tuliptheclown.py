#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

from lib.doolally import (
    Schema,
    String,
    StaticTypeArray,
    Number,
    union_with_null,
)
from schemas import hexstring_of_length
from schemas.validators import (
    isotimestamp_val,
    javascript_date_val,
    time_val,
)

CONTACT_ID = hexstring_of_length(32)
REVIEW_ID = hexstring_of_length(32)


class NewMessageReq(Schema):
    jsonschema_description = "contact by number request payload"

    name = String(required=True,
                  description="self identifying name of person",
                  min_length=2,
                  max_length=32)
    phone_or_email = String(
        required=True, description="self described phone or email of person")
    message = String(required=True,
                     description="message from person",
                     min_length=2,
                     max_length=8192)


class Message(Schema):
    jsonschema_description = "an individual message stored on the server"

    name = String(required=True,
                  description="self identifying name of person",
                  min_length=2,
                  max_length=32)
    phone_or_email = String(
        required=True, description="self described phone or email of person")
    contact_id = CONTACT_ID(required=True,
                            description="contact id of individual")
    message = String(required=True,
                     description="message from person",
                     min_length=2,
                     max_length=4096)
    creation_time = String(required=True,
                           description="timestamp message was created",
                           validator=isotimestamp_val)


class MessagesResp(Schema):
    jsonschema_description = "array of messages received by server"

    messages = StaticTypeArray(required=True,
                               element_field=Message(),
                               description="an individual message")


class ContactQueryResp(Schema):
    jsonschema_description = "contact query to see if session_id has been used"

    time_remaining = Number(
        required=True,
        description=
        "time remaining in seconds before another request can be sent",
        signed=False)


class NewContactReq(Schema):
    jsonschema_description = "create a new contact in DB"

    name = String(required=True,
                  description="name of person",
                  min_length=4,
                  max_length=64)
    phoneOrEmail = String(required=True, description="contact string")


class NewContactResp(Schema):
    jsonschema_description = "create a new contact response - contains contact_id"

    contact_id = CONTACT_ID(required=True,
                            description="contact_id of created contact")


class NewEventReq(Schema):
    jsonschema_description = "data to create a new event"

    name = String(required=True, description="name of contact")
    phone_or_email = String(required=True,
                            description="phone or email of contact")
    date = String(required=True,
                  description="date of event",
                  validator=javascript_date_val)
    start_time = String(required=True,
                        description="start time of event",
                        validator=time_val)
    end_time = String(required=True,
                      description="end time of event",
                      validator=time_val)
    description = String(required=True,
                         description="description of event",
                         min_length=1,
                         max_length=4096)
    total_price = Number(required=True,
                         description="total price of event",
                         min_value=0)
    deposit = Number(required=True,
                     description="deposit amount of event",
                     min_value=0)


class NewEventResp(Schema):
    jsonschema_description = "response of newly created event"

    event_id = String(required=True,
                      description="event_id urlsafe b64 encoded")
    user_token = String(required=True,
                        description="user token, urlsafe b64 encoded")


class Review(Schema):
    jsonschema_description = "stored review"

    review = String(required=True, description="review")
    creation_time = String(required=True,
                           description="creation time of review",
                           validator=isotimestamp_val)

    response = union_with_null(
        required=True,
        element_fields=[String(description="response by tulip")])

    response_time = union_with_null(
        required=True, element_fields=[String(validator=isotimestamp_val)])


def event_date_val(ctx_err, value):
    try:
        datetime.strptime(value, "%a %d %b %Y")
    except Exception as exc:
        raise ctx_err(str(exc))


class EventResp(Schema):
    jsonschema_description = "event response for an individual event"

    date = String(required=True,
                  description="date of event",
                  validator=event_date_val)
    start_time = String(required=True,
                        description="start time of event",
                        validator=time_val)
    end_time = String(required=True,
                      description="end time of event",
                      validator=time_val)
    description = String(required=True,
                         description="description of event",
                         min_length=1,
                         max_length=4096)
    total_price = Number(required=True,
                         description="total price of event",
                         min_value=0)
    deposit = Number(required=True,
                     description="deposit amount of event",
                     min_value=0)

    review = union_with_null(required=True, element_fields=[Review()])


class EventSingle(Schema):
    jsonschema_description = "single event for events admin screen"

    date = String(required=True,
                  description="date of event",
                  validator=event_date_val)
    start_time = String(required=True,
                        description="start time of event",
                        validator=time_val)
    end_time = String(required=True,
                      description="end time of event",
                      validator=time_val)
    description = String(required=True,
                         description="description of event",
                         min_length=1)
    event_id = String(required=True,
                      description="event_id urlsafe b64 encoded")
    user_token = String(required=True,
                        description="user token, urlsafe b64 encoded")


class EventsResp(Schema):
    jsonschema_description = "all events"

    events = StaticTypeArray(required=True, element_field=EventSingle())


class NewReviewReq(Schema):
    jsonschema_description = "new review"

    review = String(required=True,
                    min_length=1,
                    max_length=4096,
                    description="review to be posted")
    event_id = String(required=True,
                      min_length=16,
                      description="event to which review is attached")


class NewReviewResp(Schema):
    jsonschema_description = "respond to new review with review id"

    review_id = REVIEW_ID(required=True, description="review id")


class ReviewSingle(Schema):
    review_id = REVIEW_ID(required=True)
    weight = Number(required=True, is_int=True, min_value=0, max_value=255)
    review = String(required=True)
    event_id = union_with_null(required=True, element_fields=[String()])
    user_token = union_with_null(required=True, element_fields=[String()])


class ReviewsResp(Schema):
    reviews = StaticTypeArray(required=True, element_field=ReviewSingle())


class NewReviewResponseReq(Schema):
    jsonschema_description = "respond to an exisitng review"

    review_id = REVIEW_ID(required=True, description="review id")
    weight = Number(required=True,
                    is_int=True,
                    min_value=0,
                    max_value=255,
                    description="weight")
    response = union_with_null(
        required=True,
        element_fields=[
            String(max_length=4096, description="tulip response to comment"),
        ])
