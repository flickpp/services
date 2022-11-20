#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime

from peewee import (
    Model,
    Field,
    CharField,
    AutoField,
    DateField,
    TimeField,
    ForeignKeyField,
    DateTimeField,
    SmallIntegerField,
    FloatField,
    MySQLDatabase,
)

from models import (
    DB_HOST,
    DB_PORT,
    Binary8,
    Binary16,
    Binary32,
    varbinary_field,
)

DB = MySQLDatabase('TULIPTHECLOWN',
                   user='tuliptheclown',
                   host=DB_HOST,
                   port=DB_PORT,
                   password="password")


class ContactType(Field):
    field_type = 'smallint'

    def db_value(self, value):
        if value == "email":
            return 0
        elif value == "phone":
            return 1
        else:
            raise ValueError("expected email or phone")

    def python_value(self, value):
        if value == 0:
            return "email"
        elif value == 1:
            return "phone"
        else:
            raise ValueError("expected email or phone")


class Contact(Model):
    contact_id = Binary16(primary_key=True)
    name_ = varbinary_field("Name", 64)(null=False)
    xor_key = Binary8(null=False)
    contact_type = ContactType(null=False)
    phone_or_email = CharField(null=False, max_length=128)

    class Meta:
        database = DB
        table_name = "Contact"


class Message(Model):
    message_key = AutoField(primary_key=True)
    contact_id = ForeignKeyField(Contact, null=False, backref='message')
    message = varbinary_field("Message", 8192)(null=False)
    xor_key = Binary16(null=False)
    creation_time = DateTimeField(null=False, default=datetime.now)

    class Meta:
        database = DB
        table_name = "Message"


class Review(Model):
    review_id = Binary16(primary_key=True)
    contact_id = ForeignKeyField(Contact, backref='review')
    review = varbinary_field("Review", 8192)(null=False)
    xor_key = Binary16(null=False)
    weight = SmallIntegerField(null=False, default=lambda: 0)
    response = varbinary_field("Response", 4096)(null=True,
                                                 default=lambda: None)
    creation_time = DateTimeField(null=False, default=datetime.now)
    response_time = DateTimeField(null=True, default=lambda: None)

    class Meta:
        database = DB
        table_name = "Review"


class Event(Model):
    event_id = Binary16(primary_key=True)
    contact_id = ForeignKeyField(Contact, null=False, backref='event')
    review_id = ForeignKeyField(Review,
                                null=True,
                                default=lambda: None,
                                backref='event')
    date_ = DateField(null=False)
    start_time = TimeField(null=False)
    end_time = TimeField(null=False)
    description = varbinary_field("Description", 8192)(null=False)
    total_price = FloatField(null=False)
    deposit = FloatField(null=False)

    class Meta:
        database = DB
        table_name = "Event"
