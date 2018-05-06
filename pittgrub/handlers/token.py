import logging

from jwt import get_unverified_header

from handlers.base import BaseHandler, SecureHandler
from service.auth import JwtTokenService
from service.user import get_user, update_expo_token


class TokenRequestHandler(BaseHandler):
    required_fields = set(['token'])

    def initialize(self, token_service: JwtTokenService):
        self.token_service = token_service

    def post(self, path: str):
        token = self.get_data()['token']
        if not get_unverified_header(token).get('tok') == 'ref':
            self.write_error(401, f'Error: Refresh token required')
        else:
            user_id = self.token_service.decode_refresh_token(token).get('own')
            user = get_user(user_id)
            if user.disabled:
                self.write_error(403, f'Error: user account disabled')
            elif not user.active:
                self.write_error(401, f'Error: user activation required')
            else:
                access_token = self.token_service.create_access_token(owner=user.id)
                self.success(payload=dict(
                    user=user.json(),
                    access_token=access_token.decode()
                ))
        self.finish()


class TokenValidationHandler(BaseHandler):
    required_fields = set(['token'])

    def initialize(self, token_service: JwtTokenService):
        self.token_service = token_service

    def post(self, path: str):
        token = self.get_data().get('token')
        try:
            valid = self.token_service.validate_token(token)
            self.success(payload=dict(valid=valid))
        except:
            self.write_error(400, f'Error: Invalid token')
        self.finish()


class NotificationTokenHandler(SecureHandler):
    required_fields = set(['token'])

    def post(self, path):
        user_id = self.get_user_id()
        token = self.get_data().get('token')
        try:
            update_expo_token(user_id, token)
            self.success(204)
        except Exception as e:
            logging.error(e)
            self.write_error(500, 'Error: failed to add expo token')
        self.finish()
