import random
import string

from .base import BaseHandler, CORSHandler, SecureHandler
from handlers.response import Payload
from pittgrub.auth import decode_jwt
from pittgrub.db import FoodPreference, User, UserActivation, UserFoodPreference

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

class UserPasswordHandler(CORSHandler, SecureHandler):
    def post(self):
        user_id = self.get_jwt()['own']
        user = User.get_by_id(user_id)
        print(user.password)
        data = json_decode(self.request.body)
        if all(key in data for key in ('old_password', 'new_password')):
            if User.verify(user.email, data['old_password']):
                User.change_password(user_id, data['new_password'])
                self.success(status=200)
            else:
                self.write_error(400, 'Incorrect email or password')
        else:
            fields = ", ".join(set('old_password', 'new_password') - data.keys())
            self.write_error(400, f'Missing field(s): {fields}')

class UserPreferenceHandler(BaseHandler):
    def get(self, path):
         # check token
        authorization = self.request.headers.get('Authorization')[7:]
        if authorization:
            token = decode_jwt(authorization)
            user_id = token['own']
            user = User.get_by_id(user_id)
            preferences = user.food_preferences
            self.success(payload=Payload(preferences))
        else:
            self.write_error(403, 'Authentication is required')

    def post(self, path):
        # check token
        authorization = self.request.headers.get('Authorization')[7:]
        if authorization:
            token = decode_jwt(authorization)
            user_id = token['own']
            # decode json
            data = json_decode(self.request.body)
            preferences = data['preferences']
            # check that preferences exist
            preference_ids = [pref.id for pref in FoodPreference.get_all()]
            if all(pref in preference_ids for pref in preference_ids):
                UserFoodPreference.update(user_id, preferences)
                self.success(status=204)
            else:
                fields = ", ".join(set(preferences)-preference_ids)
                self.write_error(401, f'Food preferences not found: {fields}')
        else:
            self.write_error(403, 'Authentication is required')


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
