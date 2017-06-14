from tornado import escape, web
from tornado.escape import utf8
from tornado.util import unicode_type
from typing import Union, Dict
from handlers.response import Payload, ErrorResponse
from util import json_dict


class BaseHandler(web.RequestHandler):
    """Common handler"""

    def write(self, chunk: Union[bytes, unicode_type, Dict, Payload, object]):
        """Writes chunk to output buffer
        Reference: https://git.io/vHgiA
        """
        if self._finished:
            raise RuntimeError("Cannot write() after finish()")
        if isinstance(chunk, dict):
            chunk = escape.json_encode(chunk)
        elif isinstance(chunk, Payload):
            chunk.add('self', self.request.uri)
            chunk = chunk.json()
        elif isinstance(chunk, ErrorResponse):
            chunk = chunk.json()
        elif not isinstance(chunk, (bytes, unicode_type)):
            payload = Payload(chunk)
            payload.add('self', self.request.uri)
            chunk = payload.json()
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        chunk = utf8(chunk)
        self._write_buffer.append(chunk)

    def write_error(self, status: int, message=None):
        self.set_status(status)
        error = ErrorResponse(status, message=message)
        self.finish(error)

