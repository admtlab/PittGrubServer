"""
Admin tools handler
Author: Mark Silvis
"""

from db import AccessToken, User, UserActivation, UserReferral
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


class UserReferralHandler(CORSHandler, SecureHandler):
    def get(self, path: str):
        print(f'path: {path}')
        user_id = self.get_user_id()
        refs = UserReferral.get_referrals(user_id)
        self.success(status=200, payload=Payload(refs))

    def post(self, path: str):
        keys = ['user', 'approve']
        user_id = self.get_user_id()

        # decode json
        data = json_decode(self.request.body)

        # validate data
        if all(key in data for key in keys):
            referral = UserReferral.get_referral(data['user'])
            if referral is None:
                self.write_error(400, 'Error: referral not found')
            elif referral.reference == user_id:
                if data['approve']:
                    referral.approve()
                else:
                    referral.deny()
                self.success(status=204)
            else:
                self.write_error(403, 'Error: insufficient permission')
        else:
            # missing fields
            fields = ', '.join(set(keys) - data.keys())
            self.write_error(400, f'Error: missing field(s): {fields}')

class UserPendingReferralHandler(CORSHandler, SecureHandler):
    def get(self, path: str):
        user_id = self.get_user_id()
        refs = UserReferral.get_pending(user_id)
        self.success(status=200, payload=Payload(refs))

class UserApprovedReferralHandler(CORSHandler, SecureHandler):
    def get(self, path: str):
        print(f'path: {path}')
        user_id = self.get_user_id()
        print(f'referrals for: {user_id}')
        refs = UserReferral.get_approved(user_id)
        print(f'approved referrals: {refs}')
        self.success(status=200, payload=Payload(refs))

class AdminHandler(CORSHandler, SecureHandler):
    def post(self, path: str):
        data = json_decode(self.request.body)
        user_id = self.get_user_id()
        user = User.get_by_id(user_id)
        if user.admin:
            new_admin = User.get_by_email(data['email'])
            if new_admin is None:
                self.write_error(400, 'Error: user not found')
            else:
                new_admin.make_admin()
                self.success(204)
        else:
            self.write_error(403, 'Error: insufficient permission')