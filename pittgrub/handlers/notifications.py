"""
Handle user notifications
Author: Mark Silvis
"""
import logging

from db import User
from handlers.base import BaseHandler, CORSHandler, SecureHandler
from service.admin import is_admin
from service.notification import send_to_all_users
# from notifier import send_push_notification

from tornado.escape import json_decode


class NotificationHandler(SecureHandler):
    def post(self, path: str):
        user_id = self.get_user_id()
        if not is_admin(user_id):
            logging.warning(f'User {user_id} attempted to access {cls}')
            self.write_error(403, 'Error: Insufficient permissions')
        else:
            # get json body
            data = json_decode(self.request.body)
            # message field is required
            if not all(key in data for key in ('title', 'body')):
                self.write_error(400, f'Missing field(s): {", ".join({"title", "body"} - data.keys())}')
            else:
                notification_data = data.get('data') or dict()
                send_to_all_users(data['title'], data['body'], notification_data)
                self.success(204)


class NotificationTokenHandler(BaseHandler):
    def post(self, path):
        data = json_decode(self.request.body)
        if all(key in data for key in('user', 'token')):
            user = User.get_by_id(data['user'])
            user.add_expo_token(data['token'])
            if user.expo_token is not None:
                self.success()
            else:
                self.write_error(400, 'Error: failed to add expo token')
