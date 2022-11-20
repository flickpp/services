#!/usr/bin/env python
# -*- coding: utf-8 -*-


from lib.doolally import Schema
from schemas import hexstring_of_length

BLOB_ID = hexstring_of_length(48)


class InsertBlobResp(Schema):
    blob_id = BLOB_ID(required=True)
