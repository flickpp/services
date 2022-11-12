#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json as js
from pathlib import Path
from collections import namedtuple

from casket import logger

from framework import (
    app,
    BaseEndpoint,
    Endpoint,
    add_endpoint,
    bad_request,
    login_id_sanity,
    user_id_sanity,
    internal_sever_error,
)
from lib.tokens import CONTENT_TYPES, read_blob_token, TokenError, EXTENSIONS
from clients import sha256_monstermac, login_key

BLOBS_DIR = os.environ.get("PLANTPOT_IMAGES_BLOBS_DIR", "/blobs")
BLOBS_DIR = Path(BLOBS_DIR).absolute()


def read(blob_id, extension):
    path = BLOBS_DIR / blob_id[:2] / (blob_id[2:] + '.' + extension)
    with open(path, 'rb') as file:
        return file.read()


def write(blob_id, extension, blob):
    dir = BLOBS_DIR / blob_id[:2]

    if not dir.is_dir():
        dir.mkdir()

    name = blob_id[2:] + '.' + extension
    with open(dir / name, 'wb') as file:
        file.write(blob)


def match_insert(req):
    return req.path().lower() == "/insert" and req.method() == "POST"


def insert(req, resp):
    content_type = req.content_type()

    if not content_type:
        raise bad_request("Missing Content Type",
                          "content-type header must be present")

    extension = CONTENT_TYPES.get(content_type.lower())
    if not extension:
        raise bad_request("Invalid Content Type",
                          f"unrecognised content-type {content_type}")

    blob = req.body()
    if not blob:
        raise bad_request("Empty Body", "request body may not be empty")

    # compute the blob id
    blob_id = sha256_monstermac(blob)[:24].hex()

    # Write blob to file system
    write(blob_id, extension, blob)

    logger.info("created blob", {
        "blobId": blob_id,
    })

    # Send back blobId to client
    resp_payload = js.dumps({"blobId": blob_id})
    resp.set_header("202 Created", [("Content-Type", "application/json")])
    resp.set_content_str(resp_payload)


RetrieveResponse = namedtuple("RetrieveResponse",
                              ("status", "headers", "body_bytes"))


def retrieve(blob_tk, key):
    try:
        blob_id, content_type = read_blob_token(blob_tk, key)
        blob_id = blob_id.hex()
    except TokenError as exc:
        raise bad_request("Invalid Blob Token", str(exc))

    extension = CONTENT_TYPES.get(content_type)
    try:
        blob = read(blob_id, extension)
    except Exception as exc:
        raise internal_sever_error("Missing Blob",
                                   "couldn't find blob for issued token")

    headers = [
        ("Content-Type", content_type),
        ("Cache-Control", "private, immutable")
    ]
    return RetrieveResponse("200 Ok", headers, blob)


def match_login_retrieve(req):
    return req.path().startswith("/login") and req.method() == "GET"


def login_retrieve(blob_tk, login_id, **params):
    return retrieve(blob_tk, login_key(login_id))


def match_user_retrieve(req):
    return req.path().startswith("/user") and req.method() == "GET"


def user_retrieve(blob_tk, user_id, **params):
    return retrieve(blob_tk, login_key(user_id))


def read_blob_token_from_path(prefix):
    def inner(path):
        path = path[len(prefix + '/'):]

        if not path:
            raise bad_request("Missing Blob Token",
                              "couldn't find blob token in request path")

        return [path]

    return inner


add_endpoint(BaseEndpoint(insert, match_insert))

LOGIN_RETRIEVE = Endpoint(login_retrieve, match_login_retrieve)
LOGIN_RETRIEVE.set_path_args(read_blob_token_from_path("/login"))
LOGIN_RETRIEVE.add_url_param_arg("login_id", sanity=login_id_sanity)
add_endpoint(LOGIN_RETRIEVE)

USER_RETRIEVE = Endpoint(login_retrieve, match_user_retrieve)
USER_RETRIEVE.set_path_args(read_blob_token_from_path("/user"))
USER_RETRIEVE.add_url_param_arg("user_id", sanity=user_id_sanity)
add_endpoint(USER_RETRIEVE)
