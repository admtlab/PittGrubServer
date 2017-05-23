from tornado import escape, web
from tornado.escape import utf8
from tornado.util import unicode_type
from typing import Union, Dict
from handlers.response import Payload, ErrorResponse
from util import json_dict


class BaseHandler(web.RequestHandler):
    """Common handler"""

    def write(self, chunk: Union[bytes, unicode_type, Dict, Payload, object]):
        if self._finished:
            raise RuntimeError("Cannot write() after finish()")
        if isinstance(chunk, dict):
            chunk = escape.json_encode(chunk)
            self.set_header("Content-Type", "application/json; charset=UTF-8")
        elif isinstance(chunk, Payload):
            chunk = chunk.json()
            self.set_header("Content-Type", "application/json; charset=UTF-8")
        elif not isinstance(chunk, (bytes, unicode_type)):
            payload = Payload(chunk)
            chunk = payload.json()
            self.set_header("Content-Type", "application/json; charset=UTF-8")
        chunk = utf8(chunk)
        self._write_buffer.append(chunk)
