import os
import json as js
from collections import namedtuple

from casket import logger

from peewee import PeeweeException

from lib.doolally import validate as validate_json, ValidationError

from .endpoints import ENDPOINTS, add_endpoint
from .reqresp import (
    Request,
    Response,
    EmptyResponse,
    bad_request,
    access_denied,
    internal_sever_error,
    ErrorResponse,
    Redirect,
    JSONResponse,
    ValidationError,
    InvalidPayload,
    html_response,
)

__all__ = [
    "add_endpoint",
    "app",
    "post_json_endpoint",
    "get_endpoint",
    "EmptyResponse",
    "Redirect",
    "bad_request",
    "access_denied",
    "application",
    "ValidationError",
]


def app(environ, start_response):
    req = Request.from_environ(environ)
    resp = Response(req)

    for endpoint in ENDPOINTS:
        if endpoint(req, resp):
            if not resp.set_header_called():
                environ['wsgi.errors'].write("response object header not set")
                resp.set_header(
                    "500 No Header",
                    [("X-Error", "response object header not set")])
                resp.set_content_bytes(b"")

            break
    else:
        resp.set_not_found()

    start_response(resp.status, resp.headers)
    return resp.bytes_iter()


UrlParamArg = namedtuple("UrlParamArg", ("key", "required", "sanity"))


class BaseEndpoint:

    def __init__(self, clb, matcher=None):
        self._clb = clb
        if matcher is None:
            self._matcher = lambda req: True
        else:
            self._matcher = matcher

    def __call__(self, req, resp):
        if not self._matcher(req):
            return False

        try:
            self._call(req, resp)
        except Redirect as exc:
            headers = [("Location", exc.location)]

            resp.set_header(exc.args[0], headers)
            resp.set_content_bytes(b"")

        except ErrorResponse as exc:
            headers = []
            if exc.x_error:
                headers.append(("X-Error", exc.x_error))

            resp.set_header(exc.args[0], headers)
            resp.set_content_bytes(b"")

        return True

    def _call(self, req, resp):
        self._clb(req, resp)


class Endpoint(BaseEndpoint):
    def __init__(self, clb, matcher=None):
        super().__init__(clb, matcher)
        self._pass_context = False
        self._url_param_args = []
        self._req_body_transform = None
        self._path_args = None
        self._resp_transform = None

    def pass_context(self):
        self._pass_context = True

    def add_url_param_arg(self, key, required=True, sanity=None):
        self._url_param_args.append(UrlParamArg(key, required, sanity))

    def set_req_body_transform(self, transform):
        self._req_body_transform = transform

    def set_resp_transform(self, transform):
        self._resp_transform = transform

    def set_path_args(self, transform=None):
        if transform is None:
            transform = lambda path: path.split('/')

        self._path_args = transform

    def _call(self, req, resp):
        args = []

        if self._pass_context:
            args.append(req.ctx())

        # Do we have any path args?
        if self._path_args:
            args.extend(self._path_args(req.path(lowercase=False)))

        # Do we have any url params?
        params = req.params()
        for url_arg in self._url_param_args:
            arg_ll = params.get(url_arg.key)

            if arg_ll is None and url_arg.required:
                raise bad_request("Missing Url Param",
                                  f"required url param {url_arg.key}")

            if arg_ll is None:
                continue

            if len(arg_ll) != 1:
                raise bad_request("Duplicate Url Param",
                                  f"url param {url_arg.key} duplicated")

            if url_arg.sanity:
                err = lambda reason: bad_request("Invalid Url Param", reason)
                url_arg.sanity(err, arg_ll[0])

            args.append(arg_ll[0])
            del params[url_arg.key]

        # Do we expect a body? Any sanity checking?
        if self._req_body_transform:
            try:
                args.append(self._req_body_transform(req.body()))
            except InvalidPayload as exc:
                raise bad_request("Invalid Payload",
                                  f"invalid payload [{exc}]")

        clb_resp = self._clb(*args, **params)
        if self._resp_transform:
            clb_resp = self._resp_transform(clb_resp)

        resp.set_header(clb_resp.status, clb_resp.headers)
        resp.set_content_bytes(clb_resp.body_bytes)


class JSONSanity:

    def __init__(self, sanity):
        self._sanity = sanity

    def __call__(self, body):
        try:
            body = js.loads(body)
        except Exception as exc:
            raise InvalidPayload(f"couldn't deserialize json - {exc}")

        self._sanity(InvalidPayload, body)
        return body


def post_json_endpoint(path,
                       schema_sanity,
                       func,
                       require_session_id=True,
                       resp_schema_sanity=None,
                       require_user_id=False,
                       require_login_id=False,
                       pass_context=False):

    path = path.lower()
    endpoint = Endpoint(
        func, lambda req: req.path() == path and req.method() == "POST")

    if pass_context:
        endpoint.pass_context()

    if require_session_id:
        endpoint.add_url_param_arg("session_id", sanity=session_id_sanity)

    if require_user_id:
        endpoint.add_url_param_arg("user_id", sanity=user_id_sanity)

    if require_login_id:
        endpoint.add_url_param_arg("login_id", sanity=login_id_sanity)

    endpoint.set_req_body_transform(JSONSanity(schema_sanity))

    if resp_schema_sanity:
        endpoint.set_resp_transform(JSONResponse(resp_schema_sanity))

    add_endpoint(endpoint)


def get_endpoint(path,
                 func,
                 require_session_id=True,
                 require_user_id=False,
                 require_login_id=False,
                 pass_context=False):

    path = path.lower()
    endpoint = Endpoint(
        func, lambda req: req.path() == path and req.method() == "GET")

    if pass_context:
        endpoint.pass_context()

    if require_session_id:
        endpoint.add_url_param_arg("session_id", sanity=session_id_sanity)

    if require_user_id:
        endpoint.add_url_param_arg("user_id", sanity=user_id_sanity)

    if require_login_id:
        endpoint.add_url_param_arg("login_id", sanity=login_id_sanity)

    add_endpoint(endpoint)


def get_json_endpoint(path,
                      schema_sanity,
                      func,
                      require_session_id=True,
                      require_user_id=False,
                      require_login_id=False,
                      pass_context=False):

    path = path.lower()
    endpoint = Endpoint(
        func, lambda req: req.path() == path and req.method() == "GET")

    if pass_context:
        endpoint.pass_context()

    if require_session_id:
        endpoint.add_url_param_arg("session_id", sanity=session_id_sanity)

    if require_user_id:
        endpoint.add_url_param_arg("user_id", sanity=user_id_sanity)

    if require_login_id:
        endpoint.add_url_param_arg("login_id", sanity=login_id_sanity)

    endpoint.set_resp_transform(JSONResponse(schema_sanity))

    add_endpoint(endpoint)


def get_html_endpoint(path, func, pass_context=False, require_session_id=True):
    path = path.lower()

    endpoint = Endpoint(
        func, lambda req: req.path() == path and req.method() == "GET")

    if pass_context:
        endpoint.pass_context()

    if require_session_id:
        endpoint.add_url_param_arg("session_id", sanity=session_id_sanity)

    endpoint.set_resp_transform(html_response)

    add_endpoint(endpoint)


def session_id_sanity(err, val):
    if len(val) != 32 or not is_hexstring(val):
        raise err("session id must be a hexstring of length 32 chars")


def user_id_sanity(err, val):
    if len(val) != 32 or not is_hexstring(val):
        raise err("user id must be a hexstring of length 32 chars")


def login_id_sanity(err, val):
    if len(val) != 32 or not is_hexstring(val):
        raise err("login id must be a hexstring of length 32 chars")


def is_hexstring(val):
    for c in val:
        if c not in "0123456789abcdef":
            return False

    return True
