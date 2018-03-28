"""
Index handler
Author: Mark Silvis
"""


import logging

from __init__ import __version__
from db import health_check
from handlers.base import BaseHandler

from tornado.escape import json_encode


class HealthHandler(BaseHandler):
    """Health status of server"""

    def get(self, path):
        logging.info("Health status check")
        db_status = 'OK' if health_check() else 'WARN'
        status = {
            'version': __version__,
            'status': 'up',
            'database': db_status
        }
        self.write(json_encode(status))
        self.finish()


class MainHandler(BaseHandler):
    """Welcome message"""

    def get(self, path):
        logging.info("Sending welcome message")
        message = {
            'message': 'Greeting from the PittGrub team!'
        }
        self.write(json_encode(message))
        self.finish()


class TestHandler(BaseHandler):

    def get(self, path):
        logging.info('\n\nIn Test Handler')
        self.set_status(200)
        self.finish()
        logging.info('Done\n\n')
