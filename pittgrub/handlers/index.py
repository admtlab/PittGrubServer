"""
Index handler
Author: Mark Silvis
"""


import logging

from __init__ import __version__
from db import health_check
from handlers.base import BaseHandler
from util import json_esc


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
