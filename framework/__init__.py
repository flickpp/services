import os
import json as js

from casket import logger

from peewee import PeeweeException

from lib.doolally import validate as validate_json, ValidationError

from .endpoints import ENDPOINTS, add_endpoint
from .reqresp import Request, Response, EmptyResponse, bad_request, ErrorResponse



__all__ = [
    "add_endpoint",
    "app",
    "post_json_endpoint",
    "EmptyResponse",
    "bad_request",
    "application",
]

def app(environ, start_response):
    req = Request.from_environ(environ)
    resp = Response(req)

    for endpoint in ENDPOINTS:
        if endpoint(req, resp):
            if not resp.set_header_called():
                environ['wsgi.errors'].write("response object header not set")
                resp.set_header("500 No Header", [("X-Error", "response object header not set")])
                resp.set_content_bytes(b"")

            break
    else:
        resp.set_not_found()

    start_response(resp.status, resp.headers)
    return resp.bytes_iter()


def post_json_endpoint(path, schema, func, require_session_id=True):
    def endpoint(req, resp):
        if req.path() != path or req.method() != "POST":
            return False

        args = [req.ctx()]

        if require_session_id:
            try:
                args.append(get_session_id(req.params()))
                del req.params()['session_id']
            except Exception:
                logger.error("missing/invalid session_id")
                resp.set_header("400 Invalid Session Id")
                resp.set_content_bytes(b"")
                return True

        try:
            body = js.loads(req.body())
            validate_json(body, schema)
            args.append(body)
        except Exception as exc:
            resp.set_header("400 Invalid Body", [("X-Error", str(exc))])
            resp.set_content_bytes(b"")
            return True

        try:
            empty_resp = func(*args, **req.params())

        except ErrorResponse as exc:
            headers = []
            if exc.x_error:
                headers.append(("X-Error", exc.x_error))
                resp.set_header(exc.args[0], headers)
                resp.set_content_bytes(b"")
                return True

        except PeeweeException as exc:
            resp.set_header("500 DB I/O Failed", [("X-Error", str(exc))])
            resp.set_content_bytes(b"")
            return True

            
        resp.set_header(empty_resp.status, empty_resp.headers)
        resp.set_content_bytes(b"")

        return True

    add_endpoint(endpoint)


def get_json_endpoint(path, schema, func, require_session_id=True):
    def endpoint(req, resp):
        if req.path() != path or req.method() != "GET":
            return False

        args = [req.ctx]
        if require_session_id:
            try:
                args.append(get_session_id(req.params()))
                del req.params()['session_id']
            except Exception:
                logger.error("missing/invalid session_id")
                resp.set_header("400 Invalid Session Id")
                resp.set_content_bytes(b"")
                return True

        try:
            resp_json = func(*args, **req.params())

        except ErrorResponse as exc:
            headers = []
            if exc.x_error:
                headers.append(("X-Error", exc.x_error))

            resp.set_header(exc.args[0], headers)
            resp.set_content_bytes(b"")
            return True

        except PeeweeException as exc:
            resp.set_header("500 DB I/O Failed", [("X-Error", str(exc))])
            resp.set_content_bytes(b"")
            return True

        try:
            validate_json(resp_json, schema)
        except ValidationError as exc:
            logger.error("invalid response json", {
                "error": str(exc),
            })
            resp.set_header("500 Invalid JSON response", [
                ("X-Error", str(exc)),
            ])
            resp.set_content_bytes(b"")
            return True

        resp.set_header("200 Ok", [
            ("Content-Type", "application/json"),
        ])
        resp.set_content_str(js.dumps(resp_json))

        return True

    add_endpoint(endpoint)


def get_session_id(params):
    session_id = params['session_id']
    assert(len(session_id) == 1)
    validate_session_id(session_id[0])
    return session_id[0]


def validate_session_id(session_id):
    if len(session_id) != 32:
        raise ValueError

    for c in session_id:
        if c not in "0123456789abcdef":
            print("ici2")
            raise ValueError
