import base64
import logging
from datetime import datetime, timedelta

from .base import BaseHandler, CORSHandler, SecureHandler
from auth import create_jwt, decode_jwt
from db import FoodPreference, User, UserVerification, UserFoodPreference
from email import send_verification_email, send_password_reset_email
from handlers.response import Payload

from tornado.escape import json_decode, json_encode
from tornado.web import MissingArgumentError


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
        user_id = self.get_jwt()['own']
        user = User.get_by_id(user_id)
        print(user.password)
        data = json_decode(self.request.body)
        if all(key in data for key in ('old_password', 'new_password')):
            if User.verify_credentials(user.email, data['old_password']):
                User.change_password(user_id, data['new_password'])
                self.success(status=200)
            else:
                self.write_error(400, 'Incorrect email or password')
        else:
            fields = ", ".join(set('old_password', 'new_password') - data.keys())
            self.write_error(400, f'Missing field(s): {fields}')


class UserPasswordResetHandler(CORSHandler):
    def post(self, path):
        # user forgot password
        # we need to generate a one-time use reset token
        # and email them a password reset link
        data = json_decode(self.request.body)
        if 'email' in data:
            # they are requesting the reset link
            user = User.get_by_email(data['email'])
            if user:
                jwt_token = create_jwt(
                    owner=user.id, secret=user.password, expires=datetime.utcnow() + timedelta(hours=24))
                encoded = base64.b64encode(jwt_token)
                send_password_reset_email(to: user.email, token=encoded)
                self.success(status=204)
            else:
                self.write_error(400, 'No user exists with that email address')
        elif 'token' in data and 'password' in data:
            # they are sending their token and new password
            # set them up with the change
            pass
        else:
            self.write_error(400, 'Missing fields')


class UserPreferenceHandler(SecureHandler):
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
        user_id = self.get_jwt()['own']
        user = User.get_by_id(user_id)
        if user is not None:
            # decode json
            data = json_decode(self.request.body)
            logging.info(f'Updated preferences: {data}')
            # check that preferences exist
            preference_ids = [pref.id for pref in FoodPreference.get_all()]
            if all(pref in preference_ids for pref in data):
                UserFoodPreference.update(user_id, data)
                self.success(status=204)
            else:
                fields = ", ".join(set(data) - preference_ids)
                self.write_error(401, f'Food preferences not found: {fields}')


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
        user = User.get_by_id(user_id)
        verification = UserVerification.get_by_user(user_id)
        if verification is None:
            verification = UserVerification.add(user_id=user_id)
        try:
            send_verification_email(to=user.email, code=verification.code)
            self.success(status=204)
        except Exception as e:
            logging.error("Failed to send verification email")
            logging.error(e)
            self.write_error(500, "Error: failed to send verification email")
            raise(e)

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
