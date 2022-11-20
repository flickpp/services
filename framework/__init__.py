#!/usr/bin/env python
# -*- coding: utf-8 -*-

import traceback
from collections import namedtuple
from urllib.parse import parse_qs

ENDPOINTS = []

__all__ = [
    'Application',
    'HttpResponse',
    'UrlParamArg',
    'Redirect',
    'ErrorResponse',
    'bad_request',
    'forbidden',
    'internal_server_error',
    'Request',
    'Response',
]

UrlParamArg = namedtuple("UrlParamArg", ("key", "sanity"))


def app(environ, start_response):
    req = Request.from_environ(environ)
    resp = Response(req)

    try:
        for endpoint in ENDPOINTS:
            if endpoint(req, resp):
                if not resp.set_header_called():
                    err_str = "response object header not set"
                    environ['wsgi.errors'].write(err_str)
                    raise internal_server_error("No Header", err_str)

                # request handled by endpoint handler
                break
        else:
            raise not_found()

    except Redirect as exc:
        headers = [("Location", exc.location)]
        resp.set_header(exc.args[0], headers)

    except ErrorResponse as exc:
        headers = []
        if exc.x_error:
            headers.append(("X-Error", exc.x_error))

        resp.set_header(exc.args[0], headers)
        resp.set_content_bytes(b"")

    start_response(resp.status, resp.headers)
    return resp.bytes_iter()


class Application:

    def __init__(self, name):
        self.name = name

    def __call__(self, environ, start_response):
        return app(environ, start_response)

    def add_endpoint(self,
                     matcher,
                     clb,
                     populate_response,
                     pass_context=False,
                     path_parts=None,
                     pass_content_type=False,
                     pass_headers=False,
                     url_param_args=None,
                     pass_query=False,
                     req_body_transform=None):

        url_param_args = url_param_args or []

        def endpoint(req, resp):
            if not matcher(req):
                return False

            args = []
            # Full signature
            # (context, *path_parts, body, content_type, *url_param_args, *headers, **query)

            # Context
            if pass_context:
                args.append(req.ctx)

            # Path Parts
            if path_parts:
                args.extend(path_parts(req.path))

            # body
            if req_body_transform:
                args.append((req_body_transform(invalid_payload, req.body)))

            # Headers
            if pass_content_type:
                args.append(req.content_type)

            # Query Parameters
            for url_arg in url_param_args:
                values = req.params.get(url_arg.key)
                if not isinstance(values, list) or len(values) != 1:
                    raise bad_request(
                        'Bad Url Query',
                        f'expected exactly one query paramter {url_arg.key}')

                value = values[0]
                if url_arg.sanity:
                    url_arg.sanity(invalid_query_param, value)

                args.append(value)
                del req.params[url_arg.key]

            if pass_headers:
                # pass headers as *args
                args.extend(req.headers)

            try:
                if pass_query:
                    # Pass query as **kwargs
                    ret = clb(*args, **req.params)
                else:
                    ret = clb(*args)

                if isinstance(ret, ResponseException):
                    raise ret

                populate_response(resp, ret)

            except ResponseException:
                # Redirect / Bad Request etc.
                raise

            except Exception as exc:
                resp.exc_response(exc)

            return True

        ENDPOINTS.append(endpoint)


class Request:

    @classmethod
    def from_environ(cls, environ):
        self = cls()
        self._environ = environ
        self._body = None
        self._params = None
        self._qs = self._environ.get("QUERY_STRING", "")

        self._headers = []
        for (k, v) in environ.items():
            if k.startswith('HTTP_'):
                pair = (k[len('HTTP_'):], v)
                self._headers.append(pair)

        return self

    @property
    def path(self):
        return self._environ['PATH_INFO']

    @property
    def params(self):
        if self._params is None:
            self._params = parse_qs(self._qs)

        return self._params

    @property
    def method(self):
        return self._environ['REQUEST_METHOD']

    @property
    def headers(self):
        return self._headers

    @property
    def content_type(self):
        return self._environ.get("CONTENT_TYPE")

    @property
    def body(self):
        if self._body is None:
            self._body = self._environ['wsgi.input'].read()

        return self._body

    @property
    def ctx(self):
        return self._environ['casket.trace_ctx']


class Response:

    def __init__(self, req):
        self._req = req
        self._status = None
        self._headers = None
        self._body = b''
        self._bytes_iter = None

    def set_header(self, status, headers):
        self._status = status
        self._headers = headers

    def set_header_called(self):
        return self._status is not None

    def set_content_bytes(self, body):
        self._body = body

    def set_content_str(self, body):
        self._body = bytes(body, encoding='utf8')

    @property
    def status(self):
        return self._status

    def exc_response(self, exc):
        self._status = "500 Application Crashed"
        tb = traceback.TracebackException.from_exception(exc)
        payload = "".join(tb.format())
        payload = bytes(payload, encoding='utf8')
        self._content_length = len(payload)
        self._headers = [
            ("X-Error", f"{str(type(exc))} - {exc}"),
            ("Content-Type", "text/plain; encoding=UTF-8"),
        ]
        self._body = payload

    @property
    def headers(self):
        headers = self._headers or []

        if self._bytes_iter is None:
            for (k, v) in headers:
                if k.lower() == "content-length":
                    break
            else:
                headers.append(("Content-Length", str(len(self._body))))

        return headers

    def set_bytes_iter(self, bytes_iter):
        self._bytes_iter = bytes_iter

    def bytes_iter(self):
        if self._bytes_iter:
            return self._bytes_iter

        return (self._body, )


class ResponseException(Exception):
    pass


class Redirect(ResponseException):

    def __init__(self, location, status="303 See Other"):
        super().__init__(status)
        self.location = location


class ErrorResponse(ResponseException):

    def __init__(self, status, x_error=""):
        super().__init__(status)
        self.x_error = x_error


def bad_request(status_str, x_error):
    return ErrorResponse(f"400 {status_str}", x_error)


def forbidden(x_error):
    return ErrorResponse(f"403 Forbidden", x_error)


def internal_server_error(status_str, x_error):
    return ErrorResponse(f"500 {status_str}", x_error)


def not_found():
    return ErrorResponse("404 Not Found")


def invalid_query_param(reason):
    return bad_request("Invalid Query", reason)


def invalid_payload(reason):
    return bad_request("Invalid Payload", reason)


def already_created():
    return ErrorResponse("406 Already Created")
