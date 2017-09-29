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

from db import AccessToken, User, UserVerification, UserReferral
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
VERIFICATION_SUBJECT = "PittGrub Account Verification"
VERIFICATION_BODY = "Please verify your email address with PittGrub:"
VERIFICATION_CODE = "Your PittGrub verification code is:"
APPSTORE_LINK = 'https://appsto.re/us/dACI6.i'
PLAYSTORE_LINK = 'https://play.google.com/store/apps/details?id=host.exp.exponent'
EXPO_LINK = 'exp://exp.host/@admtlab/PittGrub'


def send_verification_email(to: str, activation: str):
    sender = 'PittGrub Support'
    # get email configuration
    config = configparser.ConfigParser()
    config.read(options.config)
    email_config = config['EMAIL']
    address = email_config.get('address')
    username = email_config.get('username')
    password = email_config.get('password')
    host = email_config.get('host')
    port = email_config.getint('port')
    html = f"{VERIFICATION_CODE} {activation}"

    # configure server
    server = smtplib.SMTP(host, port)

    # construct message information
    msg = MIMEMultipart('alternative')
    msg['Subject'] = VERIFICATION_SUBJECT
    msg['From'] = f'{sender} <{address}>'
    msg['To'] = to

    # construct message body
    # text
    text = f"""\
    Welcome to PittGrub!
    
    Your PittGrub verification code is: {activation}.
    
    Next steps:
    You're close to receiving free food! Just enter your activation code in the PittGrub app to verify your account.
    
    If you don't have the PittGrub mobile app, follow these steps to install it:
    1) Download the Expo Client app. It is available for iOS at {APPSTORE_LINK} and Android at {PLAYSTORE_LINK}.
    2) Install the PittGrub app in Expo with the following project link: {EXPO_LINK}.
    
    PittGrub is growing quickly, and we approve users daily. We will notify you when you're account has been accepted. Thanks for signing up for the PittGrub beta!


    If you've received this email in error, please reply with the details of the issue experienced.
    """

    # html
    html = f"""\
    <h2 align="center">Welcome to PittGrub!</h2>
    
    Your PittGrub verification code is: <b>{activation}</b>.
    
    <h3>Next steps</h3>
    You're close to receiving free food! Just log in to the PittGrub app with your credentials and enter your verification code when prompted.
    
    If you don't have the PittGrub mobile app, follow these steps to install it:
    <ol>
        <li>Download the Expo Client app. It is available on both <a href='{APPSTORE_LINK}'>iOS</a> and <a href='{PLAYSTORE_LINK}'>Android</a>. </li>
        <li>Install the PittGrub app in Expo with the following project link: <a href='{EXPO_LINK}'>{EXPO_LINK}</a>. </li>
    </ol>

    PittGrub is growing quickly, and we approve users daily. We will notify you when you're account has been accepted. Thanks for signing up for the PittGrub beta!
    

    <p style="color:#bbbbbb;font-size:10px">If you've received this email in error, please reply with the details of the issue experienced.</p>
    """

    # attach message body
    msg.attach(MIMEText(text, 'text'))
    msg.attach(MIMEText(html, 'html'))

    # send message
    server.ehlo()
    server.starttls()
    server.login(username, password)
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
            if user is not None:
                # add activation code
                activation = UserVerification.add(user_id=user.id)
                self.success(payload=Payload(user))
                send_verification_email(to=user.email, activation=activation.code)
            else:
                self.write_error(400, 'Error: user already exists with that email address')
        else:
            # missing required field
            fields = ", ".join(set(['email', 'password'])-data.keys())
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
                    send_verification_email(to=user.email, activation=activation.code)
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
                    self.write_error(403, 'Error: account not verified')
                else:
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
#         if User.verify_credentials(data['email'], data['password']):
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
