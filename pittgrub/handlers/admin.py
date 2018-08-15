"""
Admin tools handler
Author: Mark Silvis
"""

import logging

from tornado.escape import json_decode

from db import UserReferral
from handlers.base import CORSHandler, SecureHandler
from handlers.response import Payload
from service import MissingUserError
from service.admin import (
    host_approval, get_pending_host_requests, AdminPermissionError, get_referrals
)


class HostApprovalHandler(CORSHandler, SecureHandler):
    required_fields = set(['user_id'])

    def get(self, path: str):
        if not self.has_admin_role():
            logging.warning(f'User {self.get_user_id()} attempted to approve host')
            self.write_error(403, 'Error: insufficient permissions')
        else:
            host_requests = get_pending_host_requests()
            self.success(200, payload=Payload(host_requests))

    def post(self, path: str):
        data = self.get_data()
        user_id = data.get('user_id')
        if not isinstance(user_id, int):
            self.write(400, 'Error: invalid user id')
        else:
            admin_id = self.get_user_id()
            try:
                if not host_approval(data['user_id'], admin_id):
                    self.write_error(400, 'Error: incorrect user id')
                else:
                    self.set_status(204)
            except AdminPermissionError:
                self.write_error(403, 'Error: insufficient permissions')
            except MissingUserError:
                self.write_error(400, 'Error: User not found')
        self.finish()


class UserReferralHandler(CORSHandler, SecureHandler):
    def get(self, path: str):
        user_id = self.get_user_id()
        refs = get_referrals(user_id)
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

# class AdminHandler(CORSHandler, SecureHandler):
#     def post(self, path: str):
#         data = json_decode(self.request.body)
#         user_id = self.get_user_id()
#         user = User.get_by_id(user_id)
#         if user.admin:
#             new_admin = User.get_by_email(data['email'])
#             if new_admin is None:
#                 self.write_error(400, 'Error: user not found')
#             else:
#                 new_admin.make_admin()
#                 self.success(204)
#         else:
#             self.write_error(403, 'Error: insufficient permission')
