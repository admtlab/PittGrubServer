from tornado import escape, web
from tornado.web import Finish
from tornado.escape import utf8
from tornado.util import unicode_type
from typing import Dict, List, Optional, TypeVar, Union
from handlers.response import Payload, ErrorResponse
from util import json_dict
from auth import decode_jwt, verify_jwt
from jwt import DecodeError, ExpiredSignatureError

# typing
Writable = TypeVar('Writable', bytes, unicode_type, Dict, Payload, object)


class BaseHandler(web.RequestHandler):
    """Common handler"""

    def success(self, status: int=200, payload: Writable=None):
        """Successful request
        status: HTTP status (default: 200)
        payload: data to send (must be JSON encodable) (default: None)
        """
        self.set_status(status)
        if payload is not None:
            self.write(payload)
        self.finish()

    def write(self, chunk: Writable):
        """Writes chunk to output buffer
        Reference: https://git.io/vHgiA
        chunk: data to write (must be JSON encodable)
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

    def write_error(self, status: int, message: str=None):
        """Prepare error response
        status: HTTP status
        message: message to send (default: None)
        """
        self.set_status(status)
        error = ErrorResponse(status, message=message)
        self.write(error)

class CORSHandler(BaseHandler):
    """Cross-Origin Request Handler
    Enables cross-origin requests for endpoint
    """

    def set_default_headers(self):
        print('setting cors headers')
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", 'Content-Type, Authorization')
        self.set_header("Access-Control-Allow-Methods", 'GET, POST, PUT, PATCH, DELETE, OPTIONS')

    def options(self, path: str=None):
        self.set_status(204)
        self.finish()

class SecureHandler(BaseHandler):
    """Secure resource handler
    Verifies authentication prior to completing request
    """

    def prepare(self):
        if not self.request.method == 'OPTIONS':   # maybe not?
            try:
                if not self.verify_jwt():
                    self.write_error(403, 'Authorization token is expired')
                    raise Finish()
            except:
                self.write_error(400, 'Invalid token')
                raise Finish()

    def get_jwt(self, verify: bool=False) -> Optional[Dict[str, Union[int, str, 'datetime']]]:
        """Retrieve decoded JSON web token
        verify: verify JWT expiration (default: False)
        """
        auth = self.request.headers.get('Authorization')
        if auth is not None and auth.startswith('Bearer '):
            jwt = auth[7:]  # remove 'Bearer '
            return decode_jwt(jwt, verify)
        return None

    def verify_jwt(self) -> Optional[bool]:
        """Verify JWT is not expired
        return: True if not expired
                False if expired
        :raises DecodeError: if token fails to be decoded
        """
        try:
            if self.get_jwt(True) is not None:
                return True
        except ExpiredSignatureError:
            return False
        except DecodeError:
            raise

    def get_user_id(self) -> int:
        """Get user id from JWT
        return: user id
        """
        return self.get_jwt()['own']