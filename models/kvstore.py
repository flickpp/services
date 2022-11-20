from peewee import Model, Field, CharField, DateTimeField, MySQLDatabase

from models import DB_HOST, DB_PORT, Binary16, Binary32

DB = MySQLDatabase('KVSTORE',
                   user='kvstore',
                   host=DB_HOST,
                   port=DB_PORT,
                   password="password")


class Value(Model):
    key_hash = Binary16(primary_key=True)
    xor_key = Binary32(null=False)
    value_str = CharField(max_length=512, null=False)
    expiry_time = DateTimeField(null=False)

    class Meta:
        database = DB
        table_name = "Value"
