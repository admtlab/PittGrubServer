"""
Login and token handler
Author: Mark Silvis
"""


import logging
from datetime import datetime
import dateutil.parser
from copy import deepcopy
from db import User
from handlers.response import Payload, ErrorResponse
from handlers.base import BaseHandler
from requests.exceptions import ConnectionError, HTTPError
import json
import time
from util import json_esc

try:
    import tornado
except ModuleNotFoundError:
    # DB10 fix
    sys.path.insert(0, '/afs/cs.pitt.edu/projects/admt/web/sites/db10/beacons/python/site-packages/')
finally:
    from typing import Any, List, Dict
    from tornado import web, gen
    from tornado.escape import json_encode, json_decode


class SignUpHandler(BaseHandler):
    def post(self, path: str):
        # new user signup
        pass


class TokenHandler(BaseHandler):
    def post(self, path: str):
        # request token
        data = json_decode(self.request.body)
        if User.verify(data['email'], data['password']):
            payload = dict({'user': User.get_by_email(data['email']).id})
            self.success(payload=payload)
        else:
            self.write_error(401, f'Incorrect email or password')


class TokenValidationHandler(BaseHandler):
    def get(self, path: str) -> bool:
        # verify token
        pass


class TokenRefreshHandler(BaseHandler):
    def post(self, path: str):
        # refresh token
        pass