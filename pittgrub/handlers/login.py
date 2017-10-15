"""
Login and token handler
Author: Mark Silvis
"""

import dateutil.parser
import json
import logging
import time
from base64 import b64encode, b64decode
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any, Dict, List, Union
from uuid import uuid4

from db import AccessToken, User, UserVerification, UserReferral
from auth import create_jwt, decode_jwt, verify_jwt
from handlers.response import Payload, ErrorResponse
from handlers.base import BaseHandler, CORSHandler, SecureHandler
from verification import send_verification_email

import jwt
from jwt import DecodeError, ExpiredSignatureError
from tornado import gen, web
from tornado.escape import json_decode, json_encode


class SignupHandler(CORSHandler):

    def post(self, path: str):
        # new user signup
        # decode json
        data = json_decode(self.request.body)
        # validate data
        if all(key in data for key in ('email', 'password')):
            # add user
            user = User.add(data['email'], data['password'])
            if user is not None:
                # add activation code
                activation = UserVerification.add(user_id=user.id)
                self.success(payload=Payload(user))
                send_verification_email(to=user.email, code=activation.code)
            else:
                self.write_error(400, 'Error: user already exists with that email address')
        else:
            # missing required field
            fields = ", ".join({'email', 'password'}-data.keys())
            self.write_error(400, f'Error: missing field(s) {fields}')

class ReferralHandler(CORSHandler):

    def post(self, path: str):
        required = ['email', 'password', 'referral']
        # new user signup with referral
        # decode json
        data = json_decode(self.request.body)
        print(f'data: {data}')
        # validate data
        if all(key in data for key in required):
            # verify referral exists
            reference = User.get_by_email(data['referral'])
            if not reference:
                self.write_error(400, 'Error: referral not found')
            else:
                # add user
                user = User.add(data['email'], data['password'])
                if user is not None:
                    user_referral = UserReferral.add(user.id, reference.id)
                    activation = UserVerification.add(user_id=user.id)
                    self.success(payload=Payload(user))
                    send_verification_email(to=user.email, code=activation.code)
                else:
                    self.write_error(400, 'Error: user already exists with that email address')
        else:
            fields = ", ".join(set(required)-data.keys())
            self.write_error(400, f'Error: missing field(s) {fields}')


class LoginHandler(CORSHandler):
    def post(self, path):
        data = json_decode(self.request.body)
        if all(key in data for key in ('email', 'password')):
            if User.verify_credentials(data['email'], data['password']):
                user = User.get_by_email(data['email'])
                if not user.active:
                    activation = UserVerification.get_by_user(user.id)
                    if not activation:
                        activation = UserVerification.add(user_id=user.id)
                        send_verification_email(to=data['email'], activation=activation.code)
                    # don't want to error, just include activation status in response
                    # self.write_error(403, 'Error: account not verified')
                jwt_token = create_jwt(owner=user.id)
                decoded = decode_jwt(jwt_token)
                self.success(payload=dict(user=user.json(deep=False),
                                          token=jwt_token.decode(),
                                          expires=decoded['exp'],
                                          issued=decoded['iat'],
                                          type=decoded['tok']))
                User.increment_login(user.id)
            else:
                self.write_error(400, 'Incorrect username or password')
        else:
            fields = ", ".join({'email', 'password'}-data.keys())
            self.write_error(400, f'Error: missing field(s) {fields}')


class LogoutHandler(BaseHandler):
    def get(self, path):
        auth = self.request.headers.get('Authorization')
        if auth:
            if not auth.startswith('Bearer '):
                self.write_error(400, f'Malformed authorization header')
                return
            # remove 'Bearer'
            auth = auth[7:]
            decoded = decode_jwt(auth)
            AccessToken.delete(decoded['id'])
            self.success(payload="Successfully logged out")
        else:
            self.write_error(403)

# class TokenHandler(BaseHandler):
#     def post(self, path: str):
#         # request token
#         data = json_decode(self.request.body)
#         if User.verify_credentials(data['email'], data['password']):
#             payload = dict({'user': User.get_by_email(data['email']).id})
#             self.success(payload=payload)
#         else:
#             self.write_error(401, f'Incorrect email or password')


class TokenRefreshHandler(BaseHandler):
    def get(self, path: str):
        # verify token
        auth = self.request.headers.get('Authorization')
        if auth:
            if not auth.startswith('Bearer '):
                self.write_error(400, f'Malformed authorization header')
            else:
                # remove 'Bearer'
                auth = auth[7:]
                decoded = decode_jwt(auth)
                jwt_token = create_jwt(owner=decoded['own'])
                decoded = decode_jwt(jwt_token)
                self.success(payload=dict(token=jwt_token.decode(),
                                          expires=decoded['exp'],
                                          issued=decoded['iat'],
                                          type=decoded['tok']))
        else:
            self.write_error(403)


class TokenValidationHandler(BaseHandler):
    def get(self, path: str):
        # get token
        print('**********\nin token validation handler\n**********')
        auth = self.request.headers.get('Authorization')
        if auth:
            # verify form
            if not auth.startswith('Bearer '):
                self.write_error(400, f'Malformed authorization header')
                return
            # remove 'Bearer'
            auth = auth[7:]
            try:
                decoded = decode_jwt(auth, True)
                if AccessToken.get_by_id(decoded['id']):
                    self.success(payload=dict(valid=True, expires=decoded['exp']))
                else:
                    self.success(payload=dict(valid=False))
            except ExpiredSignatureError:
                decoded = decode_jwt(auth, False)
                self.write_error(401, dict(valid=False))
            except DecodeError as e:
                print(f'error: {e}')
                self.write_error(401, f'Error reading access token')
            except Exception as e:
                print(f'error: {e}')
                self.write_error(400)
        else:
            self.write_error(403)
