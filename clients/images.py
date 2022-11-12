#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from casket import logger

from lib.tokens import CONTENT_TYPES

from requests import post


IMAGES_ADDR = os.environ.get("PLANTPOT_IMAGES_ADDR", "images:8080")
INSERT_URL = f"http://{IMAGES_ADDR}/insert"


def insert_image(blob, content_type):
    if content_type not in CONTENT_TYPES:
        raise ValueError(f"invalid content type {content_type}")

    try:
        resp = post(INSERT_URL, headers={"Content-Type": content_type}, body=blob)

        if resp.status_code != 202:
            raise Exception("did not receive 202 response from images service")
    except Exception as exc:
        raise RuntimeError("failed to insert blob into images")

    return resp.json()['blobId']
