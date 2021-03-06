import base64
import logging

from tornado.escape import json_decode
from tornado.web import Finish

from db import UserStatus
from emailer import send_verification_email, send_password_reset_email
from service.property import get_property, set_property
from service.user import (
    get_user,
    get_user_profile,
    get_user_by_email,
    get_user_verification,
    get_user_verification_code,
    update_user_password,
    update_user_profile,
    change_user_password,
    add_location,
    verify_user
)
from .base import CORSHandler, SecureHandler


class UserHandler(SecureHandler):
    """
    Get user data for requesting user
    """

    def get(self, path: str):
        user_id = self.get_user_id()
        user = get_user(user_id)
        if not user:
            logging.warning(f'User {user_id} has token but not found?')
            self.write_error(400, f'User not found with id: {user_id}')
        else:
            self.success(200, user)
        self.finish()


class UserProfileHandler(SecureHandler):

    def get(self, path):
        user_id = self.get_user_id()
        user_profile = get_user_profile(user_id)
        self.success(200, user_profile)
        self.finish()

    def post(self, path):
        user_id = self.get_user_id()
        data = self.get_data()
        logging.info(f'Updating settings for user {user_id}, settings {data}')
        food = data.get('food_preferences')
        pantry = data.get('pantry')
        eager = data.get('eagerness')

        # validate data
        if food is not None and not all([1 <= int(pref) <= 4 for pref in food]):
            fields = ", ".join(set(food) - set(range(1, 5)))
            self.write_error(400, f'Food preferences not found: {fields}')
            raise Finish()
        if pantry is not None and not isinstance(pantry, bool):
            self.write_error(400, f'Pantry value must be true or false')
            raise Finish()
        if eager is not None and (not isinstance(eager, int) or not 1 <= eager <= 5):
            self.write_error(400, f'Eagerness value must be from 1 to 5')
            raise Finish()
        update_user_profile(user_id, food, pantry, eager)
        self.success(204)
        self.finish()

class UserPasswordHandler(CORSHandler, SecureHandler):
    required_fields = set(['old_password', 'new_password'])

    def post(self):
        user_id = self.get_user_id()
        data = self.get_data()
        old_pass = data.get('old_password')
        new_pass = data.get('new_password')
        if change_user_password(user_id, old_pass, new_pass):
            self.success(status=200)
        else:
            self.write_error(400, 'Incorrect password')
        self.finish()


class UserPasswordResetHandler(CORSHandler):

    def initialize(self, token_service: 'JwtTokenService', executor: 'ThreadPoolExecutor'):
        self.token_service = token_service
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
                token = self.token_service.create_password_reset_token(user.id)
                encoded = base64.b64encode(token).decode()
                logging.info('encoded: ', encoded)
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
            owner = self.token_service.decode_password_token(token, False)['own']
            user = get_user(owner)
            if user is not None:
                try:
                    if self.token_service.validate_token(token):
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


class UserLocationHandler(SecureHandler):
    required_fields = set(['latitude', 'longitude'])

    def post(self, path):
        user_id = self.get_user_id()
        data = self.get_data()
        add_location(user_id, data['latitude'], data['longitude'], data.get('time'))
        self.success(204)
        self.finish()


class UserVerificationHandler(SecureHandler):
    def get(self, path):
        user_id = self.get_user_id()
        try:
            user = get_user(user_id)
            threshold = int(get_property('user.threshold'))
            if user.active:
                logging.info(f"User {user_id} is already active")
                self.write_error(400, "Error: user already active")
            elif user.status == "REQUESTED" and (threshold > 0 or get_user_verification_code(user_id) is not None):
                code = get_user_verification(user_id)
                send_verification_email(to=user.email, code=code)
                set_property('user.threshold', str(threshold-1))
                self.success(status=204)
            elif user.status == 'VERIFIED' or user.status == 'ACCEPTED':
                self.write_error(400, "User is already verified")
            else:
                self.write_error(403, "User has not yet been permitted")
        except Exception as e:
            logging.error("Failed to send verification email")
            logging.error(e)
            self.write_error(500, "Error: failed to send verification email")
        finally:
            self.finish()

    def post(self, path):
        # decode json
        user_id = self.get_user_id()
        data = self.get_data()
        code = data.get('code')
        if not code:
            self.write_error(400, 'Missing verification code')
        else:
            if verify_user(code, user_id):
                self.success(status=204)
            else:
                self.write_error(400, 'Invalid verification code')
        self.finish()
