import base64
import logging
from datetime import datetime, timedelta

from .base import BaseHandler, CORSHandler, SecureHandler
from service.auth import create_jwt, decode_jwt, verify_jwt
from service.user import (
    get_user,
    get_user_by_email,
    get_user_food_preferences,
    get_user_verification,
    update_user_food_preferences,
    update_user_password,
    update_user_settings,
    verify_user
)
from db import FoodPreference, User, UserFoodPreference, UserVerification
from emailer import send_verification_email, send_password_reset_email
from handlers.response import Payload

import jwt
from tornado.escape import json_decode, json_encode
from tornado.web import Finish, MissingArgumentError


class UserHandler(SecureHandler):
    def get(self, path):
        print('*****\nin users handler\n*****')
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
            print(f'writing: {value}')
            self.set_status(200)
            payload = Payload(value)
            self.finish(payload)


class UserPasswordHandler(CORSHandler, SecureHandler):
    def post(self):
        user_id = self.get_user_id()
        user = User.get_by_id(user_id)
        data = json_decode(self.request.body)
        if all(key in data for key in ('old_password', 'new_password')):
            if update_user_password(user_id, data['old_password'], data['new_password']):
                self.success(status=200)
            else:
                self.write_error(400, 'Incorrect password')
        else:
            fields = ", ".join(set('old_password', 'new_password') - data.keys())
            self.write_error(400, f'Missing field(s): {fields}')


class UserPasswordResetHandler(CORSHandler):

    def initialize(self, executor: 'ThreadPoolExecutor'):
        self.executor = executor

    def post(self, path):
        # user forgot password
        # we need to generate a one-time use reset token
        # and email them a password reset link
        data = json_decode(self.request.body)
        if 'email' in data:
            # they are requesting the reset link
            user = get_user_by_email(data['email'])
            if user:
                jwt_token = create_jwt(
                    owner=user.id, secret=user.password, expires=datetime.utcnow() + timedelta(hours=24))
                encoded = base64.b64encode(jwt_token).decode()
                self.executor.submit(send_password_reset_email, user.email, encoded)
                self.success(status=204)
            else:
                self.write_error(400, 'No user exists with that email address')
        elif 'token' in data and 'password' in data:
            # they are sending their token and new password
            # check that the token is correct, then
            # set them up with their new password
            try:
                token = base64.b64decode(data['token']).decode()
            except:
                logging.warning(f'Encountered invalid token: {data["token"]}')
                self.write_error(400, 'Password reset failed, invalid token')
                raise Finish()
            owner = jwt.decode(token, verify=False)['own']
            user = get_user(owner)
            if user is not None:
                try:
                    if verify_jwt(token, user.password):
                        password = data['password']
                        if not update_user_password(owner, password):
                            logging.error(f'Failed password reset for user {owner.id}')
                            self.write_error(500, 'Password reset failed')
                        else:
                            self.success(status=204)
                    else:
                        self.write_error(400, 'Password reset failed, token is expired')
                except Exception as e:
                    logging.error(e)
                    self.write_error(500, 'Password reset failed')
            else:
                logging.warning(f"User with id {owner} tried to reset password, but they don't exist")
                self.write_error(400, 'No user exists with that id')
        else:
            self.write_error(400, 'Missing fields')
        self.finish()


class UserSettingsHandler(SecureHandler):
    def get(self, path):
        # check token
        user_id = self.get_user_id()
        if user_id:
            user = get_user(user_id)
            settings = user.json_settings()
            self.success(payload=Payload(settings))
        else:
            self.write_error(403, 'Authentication is required')

    def post(self, path):
        user_id = self.get_user_id()
        data = json_decode(self.request.body)
        logging.info(f'Updating settings for user {user_id}, settings {data}')
        if 'food_preferences' in data:
            # ensure preference ids are legit
            if all([1 <= int(pref) <= 4 for pref in data['food_preferences']]):
                update_user_food_preferences(user_id, data['food_preferences'])
            else:
                fields = ", ".join(set(data['food_preferences']) - set(range(1, 5)))
                self.write_error(400, f'Food preferences not found: {fields}')
                raise Finish()
        pantry = None
        eager = None
        if 'pantry' in data:
            if not isinstance(data['pantry'], bool):
                self.write_error(400, f'Pantry value must be true or false')
                raise Finish()
            pantry = data['pantry']
        if 'eagerness' in data:
            if 0 < data['eagerness']:
                self.write_error(400, f'Eagerness must be greater than 0')
                raise Finish()
            eager = data['eagerness']
        update_user_settings(user_id, pantry, eager)
        self.success(status=204)


class UserPreferenceHandler(SecureHandler):

    def get(self, path):
        # check token
        user_id = self.get_user_id()
        try:
            food_preferences = get_user_food_preferences(user_id)
            self.success(payload=Payload(food_preferences))
        except Exception as e:
            logging.error(e)
            self.write_error(500, "Error getting user food preferences")
            self.finish()

    def post(self, path):
        user_id = self.get_user_id()
        data = json_decode(self.request.body)
        # ensure food preference ids are legitimate
        if all([1 <= int(pref) <= 4 for pref in data]):
            update_user_food_preferences(user_id, data)
            self.success(204)
        else:
            fields = ", ".join(set(data) - set(range(1, 5)))
            self.write_error(400, f'Food prefereneces not found: {fields}')


class UserVerificationHandler(SecureHandler):
    def get(self, path):
        # GET request support verification code as url param
        # switching to make GET request resend verification
        # try:
        #     id = self.get_query_argument('id')
        #     if User.activate(id):
        #         self.success(payload='Successfully verified account')
        #     else:
        #         self.write_error(404)
        # except MissingArgumentError:
        #     self.write_error(404)
        user_id = self.get_user_id()
        try:
            user = get_user(user_id)
            if user.active:
                logging.info(f"User {user_id} is already active")
                self.write_error(400, "Error: user already active")
            else:
                code = get_user_verification(user_id)
                send_verification_email(to=user.email, code=code)
                self.success(status=204)
        except Exception as e:
            logging.error("Failed to send verification email")
            logging.error(e)
            self.write_error(500, "Error: failed to send verification email")
        finally:
            self.finish()

    def post(self, path):
        # decode json
        data = json_decode(self.request.body)
        user_id = self.get_user_id()
        if 'code' in data:
            code = data['code']
            if verify_user(code, user_id):
                self.success(status=204)
            else:
                self.write_error(400, 'Invalid verification code')
        else:
            self.write_error(400, 'Missing verification code')
