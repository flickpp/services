#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from peewee import Field

DB_HOST = os.environ.get("PLANTPOT_DB_HOST", "db")
DB_PORT = int(os.environ.get('PLANTPOT_DB_PORT', '3306'))


class Binary8(Field):
    field_type = 'binary(8)'


class Binary16(Field):
    field_type = 'binary(16)'


class Binary32(Field):
    field_type = 'binary(32)'


class Binary64(Field):
    field_type = 'binary(64)'


def varbinary_field(name, size):
    return type(name, (Field, ), {"field_type": f"varbinary({size})"})
