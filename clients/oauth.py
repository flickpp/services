import os

from casket import logger

import requests

from schemas import LoginData
from lib.doolally import ValidationError, validate as validate_json

OAUTH_HOST = os.environ.get("PLANTPOT_OAUTH_HOST", "oauth:8080").split(':')
if len(OAUTH_HOST) == 2:
    OAUTH_PORT = int(OAUTH_HOST[1])
    OAUTH_HOST = OAUTH_HOST[0]
elif len(OAUTH_HOST) == 1:
    OAUTH_HOST = OAUTH_HOST[0]
    OAUTH_PORT = 8080
else:
    raise ValueError("invalid PLANTPOT_OAUTH_HOST value")

URL = f"http://{OAUTH_HOST}:{OAUTH_PORT}/loginData"


def retrieve(ctx, session_id):
    url = URL + '?' + f'session_id={session_id}'
    headers = {"Traceparent": traceparent(ctx)}
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            raise Exception("expected 200 Ok from oauth service")

        body = resp.json()
        validate_json(body, LoginData)
        return body

    except ValidationError as exc:
        logger.error("invalid response from oauth service", {
            "error": str(exc),
        })

        return None

    except Exception:
        return None


def traceparent(ctx):
    return f"00-{ctx.trace_id}-{ctx.span_id}-00"
