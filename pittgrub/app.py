"""
PittGrub Server
Author: Mark Silvis (marksilvis@pitt.edu)
Author: David Tsui  (dat83@pitt.edu)
"""

# python
import configparser
import logging
import os.path
import re
import sys
from typing import Dict

# modules
from pittgrub import db
from handlers.index import (
    MainHandler, NotificationTokenHandler,
    PreferenceHandler, EventHandler, RecommendedEventHandler,
    AcceptedEventHandler, AcceptEventHandler
)
from handlers.login import (
    LoginHandler, LogoutHandler, SignupHandler,
    TokenRefreshHandler, TokenValidationHandler
)
from handlers.user import (
    UserHandler, UserActivationHandler, UserPreferenceHandler
)
from handlers.events import EventImageHandler
from storage import ImageStore

# dependencies
try:
    from tornado import httpserver, log, web
    from tornado.ioloop import IOLoop
    from tornado.options import options, define, parse_command_line
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker
except ModuleNotFoundError:
    # DB10 fix
    sys.path.insert(0, '/afs/cs.pitt.edu/projects/admt/web/sites/db10/beacons/python/site-packages/')
    from tornado import httpserver, log, web
    from tornado.ioloop import IOLoop
    from tornado.options import options, define, parse_command_line
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker


# options
define("config", default="./config.ini", type=str,
       help="Config file (default: ./config.ini)")
parse_command_line()
log.enable_pretty_logging()


class App(web.Application):
    """Wrapper around Tornado web application with configuration"""

    def __init__(self, debug: bool, image_store: ImageStore, static_path: str=None, **db_config: Dict[str, str]) -> None:
        """Initialize application

        debug: debug mode enabled
        static_path: path for static files
        db_config: database config
        """

        # tornado web app
        handlers = [
            (r"/(/*)", MainHandler),            # index
            (r'/users(/*)', UserHandler),        # all users
            (r'/users/(\d+/*)', UserHandler),    # single user
            (r'/users/activate(/*)', UserActivationHandler),
            (r'/users/preferences(/*)', UserPreferenceHandler),
            (r'/token(/*)', NotificationTokenHandler),  # add notification token
            (r'/signup(/*)', SignupHandler),
            (r'/login(/*)', LoginHandler),       # log-in with credentials
            (r'/login/refresh(/*)', TokenRefreshHandler),
            (r'/login/validate(/*)', TokenValidationHandler),
            (r'/logout(/*)', LogoutHandler),
            (r'/p(/*)', PreferenceHandler),
            (r'/events(/*)', EventHandler),      # all events
            (r'/events/(\d+/*)', EventHandler),  # single event
            (r'/events/(\d+/*)/images(/*)', EventImageHandler, dict(image_store=image_store)), # event images
            (r'/events/recommended/(\d+/*)', RecommendedEventHandler),  # recommended events for a user
            (r'/events/accepted/(\d+/*)', AcceptedEventHandler),        # accepted events for a user
            (r'/events/(\d+)/accept/(\d+/*)', AcceptEventHandler),      # accept an event for a user
            # (r'/userfood(/*)', UserFoodPreferencesHandler)
        ]

        # server settings
        settings = dict(
            static_path=static_path,
            debug=debug,)
        web.Application.__init__(self, handlers, settings)

        # initialize database
        db.init(username=db_config['username'], password=db_config['password'],
                url=db_config['url'], database=db_config['database'],
                params=db_config['params'], echo=debug, generate=debug)


def main():
    """Make application"""

    # get configuration file
    if not os.path.isfile(options.config):
        sys.exit("Error: config file not found")
    config = configparser.ConfigParser()
    config.read(options.config)

    # server configuration
    server_config = config['SERVER']
    port = server_config.getint('port')
    procs = server_config.getint('procs')
    debug = server_config.getboolean('debug')

    # database configuration
    db_config = config['DB']
    username = db_config.get('username')
    password = db_config.get('password')
    url = db_config.get('url')
    database = db_config.get('database')
    if config.has_option('DB', 'options'):
        # convert options to url parameters
        params = '?' + re.sub(',\s*', '&', db_config.get('options'))
    else:
        params = ''

    # storage configuration
    store_config = config['STORE']
    image_store = ImageStore(store_config.get('images'))

    # logging configuration
    log_config = config['LOG']
    filename = log_config.get('file')
    level = log_config.get('level')
    fmt = log_config.get('format')
    logging.basicConfig(filename=filename, level=level, format=fmt)

    # start server
    app = App(debug, image_store=image_store, username=username, password=password,
              url=url, database=database, params=params)
    server = httpserver.HTTPServer(app)
    if (procs == 1):
        # single process
        server.listen(port)
        server.start()
    else:
        # multiple processes
        server.bind(port)
        server.start(procs)
    IOLoop.current().start()


if __name__ == '__main__':
    sys.exit(main())
