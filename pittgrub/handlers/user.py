import random
import string

from .response import Payload
from .base import BaseHandler
from db import User, UserActivation

try:
    from tornado.escape import json_decode, json_encode
    from tornado.web import MissingArgumentError
except ModuleNotFoundError:
    # DB10 fix
    import sys
    sys.path.insert(0, '/afs/cs.pitt.edu/projects/admt/web/sites/db10/beacons/python/site-packages/')

    from tornado.escape import json_decode, json_encode
    from tornado.web import MissingArgumentError


def create_activation_code(length: int=6) -> str:
    chars = string.ascii_uppercase + string.digits
    code = random.choices(chars, k=length)
    return ''.join(code)


class UserHandler(BaseHandler):
    def get(self, path):
        path = path.replace('/', '')
        # get data
        print('\n\nGOT PATH\n\n')
        if path:
            id = int(path)
            value = User.get_by_id(id)
        else:
            value = User.get_all()
        # response
        if value is None:
            self.write_error(404, f'User not found with id: {id}')
        else:
            self.set_status(200)
            payload = Payload(value)
            self.finish(payload)


class UserActivationHandler(BaseHandler):
    def get(self, path):
        try:
            id = self.get_query_argument('id')
            if User.activate(id):
                self.success(payload='Successfully verified account')
            else:
                self.write_error(404)
        except MissingArgumentError:
            self.write_error(404)

    def post(self, path):
        # decode json
        data = json_decode(self.request.body)
        if 'activation' in data:
            activation = data['activation']
            if User.activate(activation):
                self.success(status=204)
            else:
                self.write_error(400, 'Invalid activation code')
        else:
            self.write_error(400, 'Missing activation code')
