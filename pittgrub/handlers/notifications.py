"""
Handle user notifications
Author: Mark Silvis
"""
import logging

from handlers.base import SecureHandler
from service.notification import send_to_all_users


class NotificationHandler(SecureHandler):
    required_fields = set(['title', 'body'])

    def post(self, path: str):
        if not self.has_admin_role():
            logging.warning(f'User {self.get_user_id()} attempted to access {cls}')
            self.write_error(403, 'Error: Insufficient permissions')
        else:
            # get json body
            data = self.get_data()
            # message field is required
            notification_data = data.get('data') or dict()
            send_to_all_users(data['title'], data['body'], notification_data)
            self.success(204)


