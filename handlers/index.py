"""
Index handler
Author: Mark Silvis
"""


import logging
from tornado import web
from tornado.escape import json_encode


class MainHandler(web.RequestHandler):
    """Hello world request"""

    def get(self):
        logging.info("Sending new message")
        message = {
            'message': 'Hello, world!'
        }
        self.write(json_encode(message))
