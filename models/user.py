#!/usr/bin/env python
# -*- coding: utf-8 -*-

from peewee import (
    MySQLDatabase,
    Model,
    Field,
    CharField,
    ForeignKeyField,
)

from models import Binary16, Binary32, Binary64

DB = MySQLDatabase('USER',
                   user='user',
                   host=DB_HOST,
                   port=DB_PORT,
                   password="password")


class LoginFlags(Field):
    field_type = 'BIT(64)'


class Login(Model):
    login_id = Binary16(primary_key=True)
    login_flags = LoginFlags(null=False)

    class Meta:
        database = DB
        table_name = "Login"


class EmailLogin(Model):
    login_id =  ForeignKeyField(Login, primary_key=True)
    email_addr = CharField(null=False, max_length=128)
    inner_salt = Binary16(null=False)
    outer_salt = Binary16(null=False)
    inner_value = Binary32(null=False)
    password_digest = Binary64(null=False)

    class Meta:
        database = DB
        table_name = "EmailLogin"
