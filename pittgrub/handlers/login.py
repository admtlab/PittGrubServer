"""
Login, signup, and token handler
Author: Mark Silvis
"""

from validate_email import validate_email

from db import UserReferral, UserVerification
from emailer import send_verification_email
from handlers.base import CORSHandler, SecureHandler
from handlers.response import Payload
from service.analytics import log_activity, Activity
from service.auth import (
    JwtTokenService,
    login,
    signup,
    host_signup
)
from service.user import get_user_by_email


class LoginHandler(CORSHandler):
    required_fields = set(['email', 'password'])

    def initialize(self, token_service: JwtTokenService):
        self.token_service = token_service

    def post(self, path):
        data = self.get_data()
        email = data['email']
        password = data['password']
        user = login(email, password)
        if user is None:
            self.write_error(400, 'Error: Incorrect email or password')
        else:
            access_token = self.token_service.create_access_token(owner=user.id)
            refresh_token = self.token_service.create_refresh_token(owner=user.id)
            self.success(payload=dict(
                user=user.json(),
                refresh_token=refresh_token.decode(),
                access_token=access_token.decode()
            ))
            log_activity(user.id, Activity.LOGIN)
        self.finish()


class LogoutHandler(SecureHandler):

    def get(self, path):
        user_id = self.get_user_id()
        log_activity(user_id, Activity.LOGOUT)
        self.success(status=200, payload="Successfully logged out\n")


class SignupHandler(CORSHandler):
    required_fields = set(['email', 'password'])

    def initialize(self, token_service: JwtTokenService):
        self.token_service = token_service

    def post(self, path: str):
        # new user signup
        # decode json
        data = self.get_data()
        # check email is valid
        if not validate_email(data['email']):
            self.write_error(400, 'Invalid email address')
        else:
            name = data['name'] if 'name' in data else None
            user, code = signup(data['email'], data['password'], name)
            if user is None or code is None:
                self.write_error(400, 'Error: user already exists with that email address')
            else:
                send_verification_email(to=user.email, code=code)
                access_token = self.token_service.create_access_token(owner=user.id)
                refresh_token = self.token_service.create_refresh_token(owner=user.id)
                self.success(payload=dict(
                    user=user.json(),
                    refresh_token=refresh_token,
                    access_token=access_token
                ))
        self.finish()


class HostSignupHandler(CORSHandler):
    required_fields = set(['email', 'password', 'name', 'organization', 'directory'])

    def initialize(self, token_service: JwtTokenService):
        self.token_service = token_service

    def post(self, path: str):
        # new user signup requesting host status
        data = self.get_data()
        # check email is valid
        if not validate_email(data['email']):
            self.write_error(400, 'Invalid email address')
        else:
            reason = data['reason'] if 'reason' in data else None
            user, code = host_signup(*[data[r] for r in self.required_fields], reason)
            if user is None or code is None:
                self.write_error(400, 'Error: user already exists with that email address')
            else:
                send_verification_email(to=user.email, code=code)
                access_token = self.token_service.create_access_token(owner=user.id)
                refresh_token = self.token_service.create_refresh_token(owner=user.id)
                self.success(payload=dict(
                    user=user.json(),
                    refresh_token=refresh_token,
                    access_token=access_token
                ))
        self.finish()


class ReferralHandler(CORSHandler):
    required_fields = set(['email', 'password', 'referral'])

    def post(self, path: str):
        # new user signup with referral
        # decode json
        data = self.get_data()
        # verify referral exists
        reference = get_user_by_email(data['referral'])
        if not reference:
            self.write_error(400, 'Error: referral not found')
        else:
            # add user
            user, activation = signup(data['email'], data['password'])
            # TODO: finish this block
            if user is not None:
                user_referral = UserReferral.add(user.id, reference.id)
                activation = UserVerification.add(user_id=user.id)
                self.success(payload=Payload(user))
                send_verification_email(to=user.email, code=activation.code)
            else:
                self.write_error(400, 'Error: user already exists with that email address')
        self.finish()
