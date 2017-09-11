"""
Login and token handler
Author: Mark Silvis
"""

import configparser
import dateutil.parser
import json
import logging
import smtplib
import time
from base64 import b64encode, b64decode
from copy import deepcopy
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Union
from uuid import uuid4

from db import AccessToken, User, UserActivation
from auth import create_jwt, decode_jwt, verify_jwt
from handlers.response import Payload, ErrorResponse
from handlers.base import BaseHandler, CORSHandler, SecureHandler

try:
    import jwt
    from jwt import DecodeError, ExpiredSignatureError
    from tornado import gen, web
    from tornado.escape import json_decode, json_encode
    from tornado.options import options
except ModuleNotFoundError:
    # DB10 fix
    import sys
    sys.path.insert(0, '/afs/cs.pitt.edu/projects/admt/web/sites/db10/beacons/python/site-packages/')

    import jwt
    from jwt import DecodeError, ExpiredSignatureError
    from tornado import gen, web
    from tornado.escape import json_decode, json_encode
    from tornado.options import options


VERIFICATION_ENDPOINT = "users/activate"
VERIFICATION_SUBJECT = "PittGrub Verification"
VERIFICATION_BODY = "Please verify your email address with PittGrub:"
VERIFICATION_CODE = "Your PittGrub verification code is:"


def send_verification_email(to: str, activation: str):
    # get email configuration
    config = configparser.ConfigParser()
    config.read(options.config)
    email_config = config['EMAIL']
    username = email_config.get('username')
    password = email_config.get('password')
    host = email_config.get('server')
    port = email_config.getint('port')
    url = config['SERVER'].get('url')
    # html = f"{VERIFICATION_BODY} https://{url}/{VERIFICATION_ENDPOINT}?id={activation}"
    html = f"{VERIFICATION_CODE} {activation}"

    # configure server
    server = smtplib.SMTP_SSL(host, port)

    # construct message
    msg = MIMEMultipart()
    msg['Subject'] = VERIFICATION_SUBJECT
    msg['From'] = username
    msg['To'] = to
    body = MIMEText(html, 'html')
    msg.attach(body)

    # send message
    server.ehlo()
    server.login(username, password)
    server.ehlo()    
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()

class SignupHandler(CORSHandler):

    def post(self, path: str):
        # new user signup
        # decode json
        data = json_decode(self.request.body)
        # validate data
        if all(key in data for key in ('email', 'password')):
            # add user
            user = User.add(data['email'], data['password'])
            if user:
                # add activation code
                activation = UserActivation.add(user=user.id)
                self.success(payload=Payload(user))
                send_verification_email(to=data['email'], activation=activation.id)
            else:
                self.write_error(400, f'User already exists with email: {data["email"]}')
        else:
            # missing required field
            fields = ", ".join(set(['email', 'password'])-data.keys())
            self.write_error(400, f'Error: missing field(s) {fields}')

class LoginHandler(CORSHandler):
    def post(self, path):
        data = json_decode(self.request.body)
        if all(key in data for key in ('email', 'password')):
            if User.verify(data['email'], data['password']):
                user = User.get_by_email(data['email'])
                jwt_token = create_jwt(owner=user.id)
                decoded = decode_jwt(jwt_token)
                self.success(payload=dict(user=user.json(deep=False),
                                          token=jwt_token.decode(),
                                          expires=decoded['exp'],
                                          issued=decoded['iat'],
                                          type=decoded['tok']))
                User.increment_login(user.id)
                if not user.active:
                    activation = UserActivation.get_by_user(user.id)
                    if not activation:
                        activation = UserActivation.add(user=user.id)
                    send_verification_email(to=data['email'], activation=activation.id)
            else:
                self.write_error(400, 'Incorrect username or password')
        else:
            fields = ", ".join(set(['email', 'password'])-data.keys())
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
#         if User.verify(data['email'], data['password']):
#             payload = dict({'user': User.get_by_email(data['email']).id})
#             self.success(payload=payload)
#         else:
#             self.write_error(401, f'Incorrect email or password')


class TokenRefreshHandler(BaseHandler):
    def get(self, path: str) -> bool:
        # verify token
        auth = self.request.headers.get('Authorization')
        if auth:
            if not auth.startswith('Bearer '):
                self.write_error(400, f'Malformed authorization header')
                return
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
