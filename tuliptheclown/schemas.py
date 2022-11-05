
from schemas import (
    Schema,
    union_with_null,
    String,
    Number,
    is_time_val,
    is_isotimestamp_val,
    javascript_date_val,
    StaticTypeArray,
    hexstring_of_length,
)


class Review(Schema):
    jsonschema_description = "stored review"

    review = String(required=True, description="review")
    creation_time = String(required=True,
                           description="creation time of review",
                           validator=is_isotimestamp_val)

    response = union_with_null(required=True,
                               element_fields=[String(description="response by tulip")])

    response_time = union_with_null(required=True,
                                    element_fields=[String(validator=is_isotimestamp_val)])


class EventResp(Schema):
    jsonschema_description = "event response for an individual event"

    date = String(required=True, description="date of event")
    start_time = String(required=True, description="start time of event", validator=is_time_val)
    end_time = String(required=True, description="end time of event", validator=is_time_val)
    description=String(required=True, description="description of event", min_length=1)
    total_price = Number(required=True, description="total price of event", min_value=0)
    deposit = Number(required=True, description="deposit amount of event", min_value=0)

    review = union_with_null(required=True,
                             element_fields=[Review()])



class EventSingle(Schema):
    jsonschema_description = "single event for events admin screen"

    date = String(required=True, description="date of event")
    start_time = String(required=True, description="start time of event", validator=is_time_val)
    end_time = String(required=True, description="end time of event", validator=is_time_val)
    description=String(required=True, description="description of event", min_length=1)
    event_id = String(required=True, description="event_id urlsafe b64 encoded")
    user_token = String(required=True, description="user token, urlsafe b64 encoded")



class EventsResp(Schema):
    jsonschema_description = "all events"

    events = StaticTypeArray(required=True,
                             element_field=EventSingle())


class ReviewSingle(Schema):
    review_id = hexstring_of_length(32, required=True)
    weight = Number(required=True, is_int=True, min_value=0, max_value=255)
    review = String(required=True)
    event_id = union_with_null(required=True, element_fields=[String()])
    user_token = union_with_null(required=True, element_fields=[String()])
    
    
class ReviewsResp(Schema):
    reviews = StaticTypeArray(required=True,
                              element_field=ReviewSingle())

class NewEventReq(Schema):
    jsonschema_description = "data to create a new event"

    name = String(required=True, description="name of contact")
    phone_or_email = String(required=True, description="phone or email of contact")
    date = String(required=True, description="date of event", validator=javascript_date_val)
    start_time = String(required=True, description="start time of event", validator=is_time_val)
    end_time = String(required=True, description="end time of event", validator=is_time_val)
    description=String(required=True, description="description of event", min_length=1, max_length=4096)
    total_price = Number(required=True, description="total price of event", min_value=0)
    deposit = Number(required=True, description="deposit amount of event", min_value=0)


class NewEventResp(Schema):
    jsonschema_description = "response of newly created event"

    event_id = String(required=True, description="event_id urlsafe b64 encoded")
    user_token = String(required=True, description="user token, urlsafe b64 encoded")


class NewMessageReq(Schema):
    jsonschema_description = "contact by number request payload"

    name = String(required=True, description="self identifying name of person", min_length=2, max_length=32)
    phone_or_email = String(required=True, description="self described phone or email of person")
    message = String(required=True, description="message from person", min_length=2, max_length=8192)

