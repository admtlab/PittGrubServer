"""
Login, signup, and token handler
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

from db import AccessToken, User, UserHostRequest, UserReferral, UserVerification, session_scope
from service.admin import host_approval
from service.auth import (
    get_access_token,
    login,
    logout,
    signup,
    host_signup,
    create_jwt,
    decode_jwt,
    verify_jwt
)
#from auth import create_jwt, decode_jwt, verify_jwt
from handlers.response import Payload, ErrorResponse
from handlers.base import BaseHandler, CORSHandler, SecureHandler
from emailer import send_verification_email

import jwt
from jwt import DecodeError, ExpiredSignatureError
from tornado import gen, web
from tornado.escape import json_decode, json_encode
from tornado.web import Finish
from validate_email import validate_email


class SignupHandler(CORSHandler):
    required = ('email', 'password')

    def post(self, path: str):
        # new user signup
        # decode json
        data = json_decode(self.request.body)
        # validate data
        if all(key in data for key in self.required):
            # check email is valid
            if not validate_email(data['email']):
                self.write_error(400, 'Invalid email address')
            else:
                name = data['name'] if 'name' in data else None
                user, activation = signup(data['email'], data['password'], name)
                if user is None or activation is None:
                    self.write_error(400, 'Error: user already exists with that email address')
                else:
                    send_verification_email(to=user.email, code=activation.code)
                    jwt_token = create_jwt(owner=user.id)
                    decoded = decode_jwt(jwt_token)
                    self.success(payload=dict(
                        user=User.to_json(user),
                        token=jwt_token.decode(),
                        expires=decoded['exp'],
                        issued=decoded['iat'],
                        type=decoded['tok']))
        else:
            # missing required field
            fields = ", ".join({*self.required}-data.keys())
            self.write_error(400, f'Error: missing field(s) {fields}')


class HostSignupHandler(CORSHandler):
    required = ('email', 'password', 'name', 'organization', 'directory')

    def post(self, path: str):
        # new user signup requesting host status
        data = json_decode(self.request.body)
        # validate data
        if all(key in data for key in self.required):
            # check email is valid
            if not validate_email(data['email']):
                self.write_error(400, 'Invalid email address')
            else:
                reason = data['reason'] if 'reason' in data else None
                user, activation = host_signup(*[data[r] for r in self.required], reason)
                if user is None or activation is None:
                    self.write_error(400, 'Error: user already exists with that email address')
                else:
                    send_verification_email(to=user.email, code=activation.code)
                    jwt_token = create_jwt(owner=user.id)
                    decoded = decode_jwt(jwt_token)
                    self.success(payload=dict(
                        user=User.to_json(user),
                        token=jwt_token.decode(),
                        expires=decoded['exp'],
                        issued=decoded['iat'],
                        type=decoded['tok']))
        else:
            # missing required field
            fields = ", ".join({*self.required}-data.keys())
            self.write_error(400, f'Error: missing field(s) {fields}')


class HostApprovalHandler(CORSHandler, SecureHandler):

    def post(self, path: str):
        data = json_decode(self.request.body)
        if not 'user_id' in data:
            self.write_error(400, 'Error: missing field(s) user_id')
        else:
            if not data['user_id'].isdecimal():
                self.write(400, 'Error: invalid user id')
            else:
                admin_id = self.get_user_id()
                try:
                    if not host_approval(data['user_id'], admin_id):
                        self.write_error(400, 'Error: incorrect user id')
                    else:
                        self.set_status(204)
                except AssertionError:
                    self.write_error(403, 'Error: insufficient permissions')
        self.finish()


class ReferralHandler(CORSHandler):

    def post(self, path: str):
        required = ['email', 'password', 'referral']
        # new user signup with referral
        # decode json
        data = self.get_data()
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
            user = login(data['email'], data['password'])
            if user is None:
                self.write_error(400, 'Incorrect username or password')
            else:
                jwt_token = create_jwt(owner=user.id)
                decoded = decode_jwt(jwt_token)
                self.success(payload=dict(
                    user=User.to_json(user),
                    token=jwt_token.decode(),
                    expires=decoded['exp'],
                    issued=decoded['iat'],
                    type=decoded['tok']))
        else:
            fields = ", ".join({'email', 'password'} - data.keys())
            self.write_error(400, f'Error: missing field(s) {fields}')


class LogoutHandler(SecureHandler):
    def get(self, path):
        jwt = self.get_jwt()
        if jwt is None:
            self.write_error(403)
        else:
            logout(jwt['id'])
            self.success(payload="Successfully logged out\n")

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
                decoded = decode_jwt(token=auth, verify_exp=True)
                if get_access_token(decoded['id']) is not None:
                    self.success(payload=dict(valid=True, expires=decoded['exp']))
                else:
                    self.success(payload=dict(valid=False))
            except ExpiredSignatureError:
                decoded = decode_jwt(token=auth, verify_exp=False)
                self.write_error(401, dict(valid=False, expires=decoded['exp']))
            except DecodeError as e:
                self.write_error(401, f'Error reading access token')
            except Exception as e:
                logging.error(e)
                self.write_error(500)
        else:
            self.write_error(403)
