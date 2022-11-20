#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from pathlib import Path

from plantpot import Plantpot, bad_request
from clients.monstermac import sha256_monstermac
from schemas.blobs import InsertBlobResp
from lib.tokens import CONTENT_TYPES

BLOBS_DIR = Path(os.environ.get('PLANTPOT_BLOBS_DIR', '/blobs')).absolute()

app = Plantpot('blobs')


@app.json(
    path='/blobs',
    pass_content_type=True,
    methods=['POST'],
    raw_body=True,
    resp_status="202 Created",
    resp_schema=InsertBlobResp,
)
def insert(body, content_type):
    if not content_type:
        raise bad_request('Missing Content Type',
                          'Content-Type header must be present')

    if not body:
        raise bad_request('Empty Body', 'Body may not be empty')

    extension = CONTENT_TYPES.get(content_type.lower())
    if not extension:
        raise bad_request('Invalid Content-Type',
                          f'Content-Type: {content_type} unrecognised')

    blob_id = sha256_monstermac(body)[:24].hex()

    write(blob_id, extension, body)

    return {
        "blobId": blob_id,
    }


def write(blob_id, extension, blob):
    dir = BLOBS_DIR / blob_id[:2]

    if not dir.is_dir():
        dir.mkdir()

    name = blob_id[2:] + '.' + extension
    with open(dir / name, 'wb') as file:
        file.write(blob)
