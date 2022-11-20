#!/usr/bin/env python
# -*- coding: utf-8 -*-


from lib.doolally import Schema, String
from schemas.validators import full_url_val


class NewLoginReq(Schema):
    current_url = String(required=True,
                         description="current url of browser",
                         validator=full_url_val)

