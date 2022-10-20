import json as js
import traceback

from casket import logger

from doolally import validate
from schemas import ContactByEmailReq, ContactByNumberReq


class Request:
    @classmethod
    def from_environ(cls, environ):
        self = cls()
        self._environ = environ
        self._body = None

        return self

    def path(self):
        return self._environ['PATH_INFO'].lower()

    def method(self):
        return self._environ['REQUEST_METHOD']

    def body(self):
        if self._body is None:
            self._body = self._environ['wsgi.input'].read()

        return self._body


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
        payload = "".join(traceback.format_exception_only(exc))
        payload = bytes(payload, encoding='utf8')
        self._content_length = len(payload)

        self._headers = [
            ("X-Error", str(exc)),
            ("Content-Type", "plain/text; encoding='utf8'"),
        ]
        self._bytes_iter = (payload,)

    def set_header(self, status, headers):
        self._status = status
        self._headers = headers

    def set_header_called(self):
        return self._status is not None

    def set_content_bytes(self, bytes):
        self._content_length = len(bytes)
        self._bytes_iter = (bytes,)

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


def contact_by_email(req, resp):
    if req.path() != "/contact/byemail" or req.method() != "POST":
        return False

    try:
        body = js.loads(req.body())
        validate(body, ContactByEmailReq)
    except Exception as exc:
        resp.bad_request_exc("invalid body", exc)
        return True

    logger.info("new contact", {
        "gdpr.email": body['email'],
        "gdpr.name": body['name'],
    })

    resp.set_header("202 Accepted", [])
    resp.set_content_bytes(b"")
    
    return True


def contact_by_phone(req, resp):
    if req.path() != "/contact/byphone" or req.method() != "POST":
        return False

    try:
        body = js.loads(req.body())
        validate(body, ContactByNumberReq)
    except Exception as exc:
        resp.bad_request_exc("invalid body", exc)
        return True

    logger.info("new contact", {
        "gdpr.phone": body['number'],
        "gdpr.name": body['name'],
    })

    resp.set_header("202 Accepted", [])
    resp.set_content_bytes(b"")
    
    return True


ENDPOINTS = [
    contact_by_email,
    contact_by_phone,
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
