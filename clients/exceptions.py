#!/usr/bin/env python
# -*- coding: utf-8 -*-


class ClientError(Exception):
    pass


class CallFailed(ClientError):
    pass


class BadResponsePayload(ClientError):
    pass
