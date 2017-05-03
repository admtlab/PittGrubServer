"""
Index handler
Author: Mark Silvis
"""


import tornado.web as web


class MainHandler(web.RequestHandler):
    """Hello world request"""

    def get(self):
        self.write("Hello, world\n")
