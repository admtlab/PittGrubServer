import logging
import re
from typing import (
    Dict,
    List,
    Optional,
    TypeVar,
    Union
)

from jwt import DecodeError, ExpiredSignatureError, get_unverified_header
from tornado import web
from tornado.escape import json_decode, utf8
from tornado.util import unicode_type
from tornado.web import Finish

from handlers.response import Payload, ErrorResponse
from service.auth import JwtTokenService
from util import json_esc

# typing
Writable = TypeVar('Writable', bytes, unicode_type, Dict, Payload, object)


class BaseHandler(web.RequestHandler):
    """Common handler"""

    def _check_https(self):
        """
        Verify HTTPS and redirect if not secure
        """
        if ('X-Forwarded-Proto' in self.request.headers and
                self.request.headers['X-Forwarded-Proto'] != 'https'):
            self.redirect(re.sub(r'^([^:]+)', 'https', self.request.full_url()))

    def _check_post_data(self):
        if self.request.method == 'POST':
            if hasattr(self, 'required_fields') and len(self.required_fields):
                data = self.get_data()
                missing_fields = ", ".join(self.required_fields - data.keys())
                if missing_fields:
                    self.write_error(400, f'Error: missing field(s) {missing_fields}')
                    raise Finish()

    def get_data(self):
        if not self.request.body:
            return dict()
        return json_decode(self.request.body)

    def prepare(self):
        super().prepare()        
        self._check_https()
        self._check_post_data()

    def success(self, status: int=200, payload: Writable=None):
        """
        Successful request
        status: HTTP status (default: 200)
        payload: data to send (must be JSON encodable) (default: None)
        """
        self.set_status(status)
        if payload is not None:
            self.write(payload)

    def write(self, chunk: Writable):
        """
        Writes chunk to output buffer
        Reference: https://git.io/vHgiA
        chunk: data to write (must be JSON encodable)
        """
        if self._finished:
            raise RuntimeError("Cannot write() after finish()")
        if isinstance(chunk, dict):
            chunk = json_esc(chunk)
        elif isinstance(chunk, Payload):
            chunk.add_link('self', self.request.uri)
            chunk = chunk.json()
        elif isinstance(chunk, ErrorResponse):
            chunk = chunk.json()
        elif not isinstance(chunk, (bytes, unicode_type)):
            payload = Payload(chunk)
            payload.add_link('self', self.request.uri)
            chunk = payload.json()
        self.set_header("Content-Type", "application/json; charset=UTF-8")
        chunk = utf8(chunk)
        self._write_buffer.append(chunk)

    def write_error(self, status: int, message: str=None):
        """
        Prepare error response
        status: HTTP status
        message: message to send (default: None)
        """
        self.set_status(status)
        error = ErrorResponse(status, message=message)
        self.write(error)


class CORSHandler(BaseHandler):
    """
    Cross-Origin Request Handler
    Enables cross-origin requests for endpoint
    Provides endpoint for option request
    """

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", 'Content-Type, Authorization')
        self.set_header("Access-Control-Allow-Methods", 'GET, POST, PUT, PATCH, DELETE, OPTIONS')

    def options(self, path: str=None):
        self.set_status(204)
        self.finish()


class SecureHandler(BaseHandler):
    """
    Secure resource handler
    Verifies authentication prior to completing request
    """

    def initialize(self, token_service: JwtTokenService):
        self.token_service = token_service

    def _check_jwt(self):
        if self.request.method != 'OPTIONS':   # maybe not?
            try:
                if not self.verify_jwt():
                    raise Finish()
            except ExpiredSignatureError:
                self.write_error(401, 'Authorization token is expired')
                raise Finish()
            except DecodeError :
                self.write_error(401, 'Invalid authorization token')
                raise Finish()
            except Exception as e:
                self.write_error(401, 'Failed to read authorization token')
                logging.warning('Failed to read authorization token\n', e)
                raise Finish()
        else:
            logging.info(f'OPTIONS headers: {self.request.headers}')

    def prepare(self):
        super().prepare()
        self._check_jwt()

    def get_jwt(self, verify: bool=False) -> Optional[Dict[str, Union[int, str, 'datetime']]]:
        """
        Retrieve decoded JSON web token
        Note: verifying JWT will result in exception if expired
        verify: verify JWT expiration (default: False)
        :return: JWT dictionary if token provided
            None if token not provided
        :raises: DecodeError if token fails to be decoded
        :raises: ExpiredSignatureError: if verifying and token is expired
        """
        auth = self.request.headers.get('Authorization')
        if auth is not None and auth.startswith('Bearer '):
            token = auth[7:]  # remove 'Bearer '
            if get_unverified_header(token).get('tok') == 'acc':
                return self.token_service.decode_access_token(token, verify)
            elif get_unverified_header(token).get('tok') == 'ref':
                return self.token_service.decode_refresh_token(token)
        return None

    def verify_jwt(self) -> Optional[bool]:
        """Verify JWT is not expired
        :return: True if not expired
            False if expired
        :raises ExpiredSignatureError: if token is expired
        :raises DecodeError: if token fails to be decoded
        """
        return self.get_jwt(True) is not None

    def get_user_id(self, verify: bool=False) -> int:
        """
        Get user id from JWT
        return: user id
        """
        return self.get_jwt(verify)['own']

    def get_roles(self) -> List[str]:
        """
        Get user roles from JWT
        :return: list of roles
        """
        return self.get_jwt()['roles'].split(",")

    def has_host_role(self) -> bool:
        """
        Check if JWT contains host role
        :return: True if token contains 'Host' role
            False if not
        """
        return 'Host' in self.get_roles()

    def has_admin_role(self) -> bool:
        """
        Check if JWT contains admin role
        :return: True if token contains 'Admin' role
            False if not
        """
        return 'Admin' in self.get_roles()
