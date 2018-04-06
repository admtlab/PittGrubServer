"""
Handle user notifications
Author: Mark Silvis
"""
import logging

from handlers.base import SecureHandler
from service.notification import send_to_all_users
from service.user import update_expo_token


class NotificationHandler(SecureHandler):
    def post(self, path: str):
        if not self.has_admin_role():
            logging.warning(f'User {self.get_user_id()} attempted to access {cls}')
            self.write_error(403, 'Error: Insufficient permissions')
        else:
            # get json body
            data = self.get_data()
            # message field is required
            if not all(key in data for key in ('title', 'body')):
                self.write_error(400, f'Missing field(s): {", ".join({"title", "body"} - data.keys())}')
            else:
                notification_data = data.get('data') or dict()
                send_to_all_users(data['title'], data['body'], notification_data)
                self.success(204)


class NotificationTokenHandler(SecureHandler):
    def post(self, path):
        user_id = self.get_user_id()
        data = self.get_data()
        if 'token' in data:
            try:
                update_expo_token(user_id, data['token'])
                self.success(204)
            except Exception as e:
                logging.error(e)
                self.write_error(500, 'Error: failed to add expo token')
        else:
            self.write_error(400, f'Token value not found')
        self.finish()

