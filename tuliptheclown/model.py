import os
from datetime import datetime

from peewee import (
    Model,
    Field,
    CharField,
    DateTimeField,
    MySQLDatabase,
    AutoField,
    ForeignKeyField,
)

DB_HOST = os.environ.get("PLANTPOT_DB_HOST", "db:3306").split(':')
if len(DB_HOST) == 2:
    DB_PORT = int(DB_HOST[1])
    DB_HOST = DB_HOST[0]

elif len(DB_HOST) == 1:
    DB_HOST = DB_HOST[0]
    DB_PORT = 3306
else:
    raise ValueError("PLANTPOT_DB_HOST invalid value")


DB = MySQLDatabase('TULIPTHECLOWN', user='tuliptheclown', host=DB_HOST, port=DB_PORT, password="password")


class ContactId(Field):
    field_type = 'binary(16)'

    def db_value(self, value):
        if isinstance(value, str):
            values = bytes.fromhex(value)
        return value

    def python_value(self, value):
        return value.hex()


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
        if value == "email":
            return 0
        elif value == "phone":
            return 1
        else:
            raise ValueError("expected email or phone")


class Contact(Model):
    contact_id = ContactId(primary_key=True)
    contact_type = ContactType(null=False)
    phone_or_email = CharField(null=False, max_length=128)

    class Meta:
        database = DB
        table_name = "Contact"


class Message(Model):
    message_id = AutoField(primary_key=True)
    contact_id = ForeignKeyField(Contact)
    name_str = CharField(null=False, max_length=128)
    message = CharField(null=False, max_length=2048 * 2)
    creation_time = DateTimeField(null=False, default=datetime.now)

    class Meta:
        database = DB
        table_name = "Message"
