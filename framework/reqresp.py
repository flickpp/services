import traceback
import json as js
from urllib.parse import parse_qs

class Request:
    @classmethod
    def from_environ(cls, environ):
        self = cls()
        self._environ = environ
        self._body = None
        self._params = None
        self._qs = self._environ.get("QUERY_STRING", "")

        return self

    def params(self):
        if self._params is None:
            self._params = parse_qs(self._qs)

        return self._params

    def path(self, lowercase=True):
        if lowercase:
            return self._environ['PATH_INFO'].lower()
        else:
            return self._environ['PATH_INFO']

    def method(self):
        return self._environ['REQUEST_METHOD']

    def content_type(self):
        return self._environ.get("CONTENT_TYPE")

    def body(self):
        if self._body is None:
            self._body = self._environ['wsgi.input'].read()

        return self._body

    def ctx(self):
        return self._environ['casket.trace_ctx']


class Response:
    def __init__(self, req):
        self._req = req
        self._status = None
        self._headers = []
        self._bytes_iter = (b"",)
        self._content_length = None

    def set_not_found(self):
        self._status = "404 Not Found"
        self._content_length = 0
        self._bytes_iter = (b"",)
        
    def bad_request_exc(self, reason, exc):
        self._status = f"400 {reason}"
        tb = traceback.TracebackException.from_exception(exc)
        payload = "".join(tb.format())
        payload = bytes(payload, encoding='utf8')
        self._content_length = len(payload)

        self._headers = [
            ("X-Error", str(exc)),
            ("Content-Type", "text/plain; charset=UTF-8"),
        ]
        self._bytes_iter = (payload,)

    def set_header(self, status, headers=None):
        headers = headers or []
        self._status = status
        self._headers = headers

    def set_header_called(self):
        return self._status is not None

    def set_content_bytes(self, bytes):
        self._content_length = len(bytes)
        self._bytes_iter = (bytes,)

    def set_content_str(self, str):
        content = bytes(str, encoding='utf8')
        self._content_length = len(content)
        self._bytes_iter = (content,)

    @property
    def headers(self):
        if self._content_length is not None:
            for (name, _) in self._headers:
                if name.lower() == "content-length":
                    break
            else:
                self._headers.append(("Content-Length", str(self._content_length)))

        return self._headers

    @property
    def status(self):
        return self._status

    def bytes_iter(self):
        return self._bytes_iter


class EmptyResponse:
    def __init__(self, status, headers):
        self.status = status
        self.headers = headers
        self.body_bytes = b""


class JSONResponse:
    def __init__(self, sanity):
        self._sanity = sanity
        self._body = None

    def __call__(self, resp):
        self._sanity(bad_json_response, resp)
        self._body = js.dumps(resp)
        return self

    @property
    def status(self):
        return "200 OK"

    @property
    def headers(self):
        return [("Content-Type", "application/json")]

    @property
    def body_bytes(self):
        if self._body is None:
            raise RuntimeError("body_bytes called on JSONResponse before being set")

        return bytes(self._body, encoding='utf8')


class HTMLResponse:
    def __init__(self, body_bytes):
        self._body_bytes = body_bytes

    @property
    def status(self):
        return "200 Ok"

    @property
    def headers(self):
        return [("Content-Type", "text/html; charset=UTF-8")]

    @property
    def body_bytes(self):
        return self._body_bytes


def html_response(resp):
    return HTMLResponse(bytes(resp, encoding='utf8'))


class Redirect(Exception):
    def __init__(self, status, location):
        super().__init__(status)
        self.location = location


class InvalidPayload(Exception):
    pass


class ValidationError(Exception):
    def __init__(self, status, x_error):
        super().__init__(status)
        self.x_error = x_error


class ErrorResponse(Exception):
    def __init__(self, status, x_error):
        super().__init__(status)
        self.x_error = x_error


def bad_request(reason, x_error=""):
    return ErrorResponse(f"400 {reason}", x_error)


def access_denied(x_error):
    return ErrorResponse("403 Access Denied", x_error)


def internal_sever_error(reason, x_error):
    return ErrorResponse(f"500 {reason}", x_error)


def bad_json_response(reason):
    return ErrorResponse("500 Bad Response", reason)
