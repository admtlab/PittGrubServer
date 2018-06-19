"""
Index handler
Author: Mark Silvis
"""


import logging

from __init__ import __version__
from db import health_check
from emailer import send_email_list_confirmation
from handlers.base import BaseHandler, CORSHandler
from service.user import add_to_email_list, remove_from_email_list
from util import json_esc
from validate_email import validate_email


class EmailListAddHandler(CORSHandler):
    def get(self, path):
        email = path.replace('/', '')

        if email and validate_email(email) and add_to_email_list(email):
            send_email_list_confirmation(email)
            self.success(200)
        else:
            self.write_error(400)
        self.finish()


class EmailListRemoveHandler(CORSHandler):
    """Remove email signup"""
    def get(self, path):
        email = path.replace('/', '')

        if email and validate_email(email) and remove_from_email_list(email):
            self.success(200, 'Success')
        else:
            self.write_error(400)
        self.finish()


class HealthHandler(BaseHandler):
    """Health status of server"""

    def get(self, path):
        logging.info("Health status check")
        status = {
            'version': __version__,
            'status': 'up',
            'database': 'OK' if health_check() else 'ERR'
        }
        self.write(json_esc(status))
        self.finish()


class MainHandler(BaseHandler):
    """Welcome message"""

    def get(self, path):
        logging.info("Sending welcome message")
        message = {
            'message': 'Greetings from the PittGrub team!'
        }
        self.write(json_esc(message))
        self.finish()
