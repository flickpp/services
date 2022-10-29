import os

from peewee import Model, Field, CharField, DateTimeField, MySQLDatabase


DB_HOST = os.environ.get("PLANTPOT_DB_HOST", "db:3306").split(':')
if len(DB_HOST) == 2:
    DB_PORT = int(DB_HOST[1])
    DB_HOST = DB_HOST[0]

elif len(DB_HOST) == 1:
    DB_HOST = DB_HOST[0]
    DB_PORT = 3306
else:
    raise ValueError("PLANTPOT_DB_HOST invalid value")


DB = MySQLDatabase('KVSTORE', user='kvstore', host=DB_HOST, port=DB_PORT, password="password")


class Binary16(Field):
    field_type = 'binary(16)'


class Binary32(Field):
    field_type = 'binary(32)'


class Value(Model):
    key_hash = Binary16(primary_key=True)
    xor_key = Binary32(null=False)
    value_str = CharField(max_length=512, null=False)
    expiry_time = DateTimeField(null=False)

    class Meta:
        database = DB
        table_name = "Value"

