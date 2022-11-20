#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

import requests

from clients.exceptions import CallFailed
from lib import traceparent
from lib.doolally import validate as validate_json
from lib.tokens import build_blob_token, CONTENT_TYPES
from schemas.blobs import InsertBlobResp

BLOBS_ADDR = os.environ.get('PLANTPOT_BLOBS_ADDR', 'blobs:8080')
BLOBS_URL = f"http://{BLOBS_ADDR}/blobs"


def insert(ctx, content_type, blob):
    headers = {
        'Traceparent': traceparent(ctx),
        'Content-Type': content_type,
    }

    try:
        resp = requests.post(BLOBS_URL, headers=headers, data=blob)
        if 'X-Error' in resp.headers:
            raise Exception(resp.headers['X-Error'])

        if resp.status_code != 202:
            raise Exception('expected 202 response code')

        body = resp.json()
        validate_json(body, InsertBlobResp)
        return body['blobId']

    except Exception as exc:
        raise CallFailed(f'failed to insert blob {exc}')

