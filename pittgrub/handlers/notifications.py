"""
Handle user notifications
Author: Mark Silvis
"""
from exponent_server_sdk import (
    PushClient, PushMessage, PushServerError, PushResponseError
)
from tornado.escape import json_decode

from db import User
from handlers.base import BaseHandler, CORSHandler, SecureHandler
from notifier import send_push_notification


class NotificationHandler(SecureHandler):
    def post(self, path: str):
        user_id = self.get_user_id()
        user = User.get_by_id(user_id)
        if user.email not in ('mas450@pitt.edu', 'marksilvis@pitt.edu'):
            self.write_error(403, 'Insufficient permissions')
        else:
            # get json body
            data = json_decode(self.request.body)
            # message field is required
            if not all(key in data for key in ('title', 'body')):
                self.write_error(400, f'Missing field(s): {", ".join({"title", "body"}-data.keys())}')
            else:
                # send message to all users
                users = User.get_all()
                for user in users:
                    if user.expo_token:
                        print(f"sending notification to user: {user.id}")
                        print(f"notification values\ntitle:{data['title']}\nbody:{data['body']}\ndata:{data.get('data')}")
                        notification_data = data.get('data') or dict()
                        notification_data['title'] = data['title']
                        notification_data['body'] = data['body']
                        notification_data['type'] = 'message'
                        send_push_notification(user.expo_token,
                                               data['title'], data['body'],
                                               notification_data)
