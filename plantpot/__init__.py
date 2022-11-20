#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json as js
from collections import namedtuple

from casket import logger

import peewee

from clients.exceptions import ClientError
from framework import (
    Application,
    UrlParamArg,
    internal_server_error,
    bad_request,
    forbidden,
    Redirect,
    already_created,
)
from lib import is_hexstring
from lib.doolally import validate as validate_json, ValidationError
from lib.tokens import TokenError

__all__ = [
    'Plantpot',
    'Redirect',
    'bad_request',
    'already_created',
    'forbidden',
    'JSONResponse',
    'HTMLResponse',
    'JSONRequest',
]

DEFAULT_CONFIG = {
    'path': "/",
    'path_prefix': None,
    'ignore_path_case': True,
    'methods': ["GET"],
    'req_transformer': None,
    'pass_context': False,
    'path_parts': None,
    'require_session_id': False,
    'require_user_id': False,
    'require_login_id': False,
    'login_id_whitelist': [],
    'pass_content_type': False,
    'pass_headers': False,
    'param_args': [],
    'pass_query': False,
    'resp_status': "200 Ok",
    'resp_content_type': None,
    'raw_body': False,
    'populate_response': None,
}


class Plantpot:

    def __init__(self, name):
        self._app = Application(name)

    def __call__(self, environ, start_response):
        return self._app(environ, start_response)

    def add_endpoint(self, clb, populate_response, **kwargs):
        config = DEFAULT_CONFIG.copy()
        for k, v in kwargs.items():
            if k not in config:
                raise KeyError(f"invalid key for registering endpoint {k}")

            config[k] = v

        if config['path_prefix'] is None:
            matcher = PathExact(config['path'],
                                methods=config['methods'],
                                ignore_case=config['ignore_path_case'])
        else:
            matcher = PathPrefix(config['path_prefix'],
                                 config['methods'],
                                 config['ignore_path_case'])

        clb = Endpoint(clb, config)
        self._app.add_endpoint(matcher, clb, populate_response,
                               **make_endpoint_kwargs(config))

        return clb

    def endpoint(self, *args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            self.add_endpoint(args[0], DefaultResponse('200 Ok'))
            return args[0]

        def inner(clb):
            populate_response = kwargs.get('populate_response',
                                           DefaultResponse('200 Ok'))
            if kwargs.get('populate_response'):
                del kwargs['populate_response']

            self.add_endpoint(clb, populate_response, **kwargs)
            return clb

        return inner

    def add_json_endpoint(self,
                          clb,
                          req_schema=None,
                          resp_schema=None,
                          **kwargs):

        if req_schema:
            kwargs['req_transformer'] = JSONRequest(req_schema)

        status = kwargs.get('resp_status', DEFAULT_CONFIG['resp_status'])
        if resp_schema:
            populate_response = JSONResponse(status, resp_schema)
        else:
            populate_response = DefaultResponse(status)

        return self.add_endpoint(clb, populate_response, **kwargs)

    def json(self, *args, req_schema=None, resp_schema=None, **kwargs):

        if len(args) == 1 and callable(args[0]) and len(kwargs) == 0:
            self.add_json_endpoint(args[0])
            return args[0]

        def inner(clb):
            return self.add_json_endpoint(clb, req_schema, resp_schema, **kwargs)

        return inner

    def add_html_endpoint(self, clb, **kwargs):
        status = kwargs.get('resp_status', DEFAULT_CONFIG['resp_status'])
        return self.add_endpoint(clb, HTMLResponse(status), **kwargs)

    def html(self, *args, **kwargs):

        if len(args) == 1 and callable(args[0]) and len(kwargs) == 0:
            self.add_html_endpoint(args[0])
            return args[0]

        def inner(clb):
            return self.add_html_endpoint(clb, **kwargs)

        return inner


class Endpoint:

    def __init__(self, clb, config):
        self._clb = clb
        self._config = config

    def __call__(self, *args, **kwargs):
        try:
            return self._clb(*args, **kwargs)

        except ValidationError as exc:
            logger.error("inner json validation failed", {
                "error": str(exc),
            })

            raise internal_server_error(
                "Bad JSON", "inner service producded invalid json")

        except TokenError as exc:
            raise forbidden(f"invalid token {exc}")

        except ClientError as exc:
            logger.error("attempted inner call to client failed", {
                "error": str(exc),
            })

            raise internal_server_error(
                "Call Failed", "attempted call to inner service failed")

        except peewee.PeeweeException as exc:
            logger.error("DB I/O failed", {
                "error": str(exc),
            })

            raise internal_server_error("DB I/O Failed", str(exc))



def make_endpoint_kwargs(config):

    url_param_args = []

    if config['require_session_id']:
        url_param_args.append(UrlParamArg("session_id", session_id_sanity))
    if config['require_user_id']:
        url_param_args.append(UrlParamArg("user_id", user_id_sanity))
    if config['require_login_id']:
        url_param_args.append(UrlParamArg("login_id", login_id_sanity))

    for param_arg in (config['param_args'] or []):
        url_param_args.append(param_arg)

    if config['req_transformer'] is None and config['raw_body']:
        config['req_transformer'] = raw_request

    return {
        'pass_context': config['pass_context'],
        'path_parts': config['path_parts'],
        'pass_content_type': config['pass_content_type'],
        'pass_headers': config['pass_headers'],
        'url_param_args': url_param_args,
        'pass_query': config['pass_query'],
        'req_body_transform': config['req_transformer'],
    }


class DefaultResponse:

    def __init__(self, status, content_type=None):
        self._status = status
        self._content_type = content_type

    def __call__(self, resp, ret):
        if ret is None:
            resp.set_header(self._status, [])
        elif isinstance(ret, (bytes, bytearray)):
            content_type = self._content_type or 'application/octet-stream'
            resp.set_header(self._status, [('Content-Type', content_type)])
            resp.set_content_bytes(ret)
        elif isinstance(ret, str):
            content_type = "text/plain; encoding=UTF-8"
            resp.set_header(self._status, [('Content-Type', content_type)])
            resp.set_content_str(ret)
        else:
            raise internal_server_error(
                'Bad Callback', 'unrecognised return type from callback')


class PathMatcher:
    pass


class PathExact(PathMatcher):

    def __init__(self, path, methods=None, ignore_case=True):
        self._methods = methods
        if ignore_case:
            self._path = path.lower()
        else:
            self._path = path
        self._ignore_case = ignore_case

    def __call__(self, req):
        if self._methods and req.method not in self._methods:
            return False

        if self._ignore_case:
            return req.path.lower() == self._path
        else:
            return req.path == self._path


def PathPrefix(PathMatcher):

    def __init__(self, path_prefix, methods=None, ignore_case=True):
        self._methods = methods
        if ignore_case:
            self._path_prefix = path_prefix.lower()
        else:
            self._path_prefix = path_prefix
        self._ignore_case = ignore_case

    def __call__(self, req):
        if self._methods and req.method not in self._methods:
            return False

        if self._ignore_case:
            return req.path.lower().startswith(self._path_prefix)
        else:
            return req.path.startswith(self._path_prefix)


def raw_request(_, body):
    return body


class JSONRequest:

    def __init__(self, schema):
        self._schema = schema

    def __call__(self, err, body):
        try:
            body = js.loads(body)
            validate_json(body, self._schema)

            return body

        except js.JSONDecodeError as exc:
            raise err(f"couldn't deserialize JSON {exc}")

        except ValidationError as exc:
            raise err(f"invalid json payload {exc}")


class JSONResponse(DefaultResponse):

    def __init__(self, status, schema):
        self._status = status
        self._schema = schema

    def __call__(self, resp, ret):
        try:
            validate_json(ret, self._schema)

            headers = [
                ("Content-Type", "application/json"),
            ]

            resp.set_header(self._status, headers)
            resp.set_content_str(js.dumps(ret))

        except ValidationError as exc:
            raise internal_server_error("Invalid Response Payload", str(exc))

        except Exception as exc:
            raise internal_server_error("Not JSON Response", str(exc))


class HTMLResponse(DefaultResponse):

    def __init__(self, status):
        self._status = status

    def __call__(self, resp, ret):
        headers = [
            ("Content-Type", "text/html; encoding=UTF-8"),
        ]
        resp.set_header(self._status, headers)
        resp.set_content_str(ret)


def session_id_sanity(err, value):
    if not is_hexstring(value) or len(value) != 32:
        raise err("invalid session id")


def user_id_sanity(err, value):
    if not is_hexstring(value) or len(value) != 32:
        raise err("invalid user id")


def login_id_sanity(err, value):
    if not is_hexstring(value) or len(value) != 32:
        raise err("invalid login id")
