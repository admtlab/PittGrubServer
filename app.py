"""
PittGrub Server
Author: Mark Silvis
Author: David Tsui
"""


import sys
import tornado.ioloop as ioloop
import tornado.web as web
import tornado.httpserver as httpserver
from handlers.index import MainHandler


def main():
    """Make application"""

    # handlers
    app = web.Application([
        (r"/", MainHandler),
    ])

    # start server
    server = httpserver.HTTPServer(app)
    server.listen(8080)
    ioloop.IOLoop.current().start()


if __name__ == '__main__':
    sys.exit(main())
