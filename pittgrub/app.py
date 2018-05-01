"""
PittGrub Server
Author: Mark Silvis (marksilvis@pitt.edu)
"""

# python
import configparser
import logging
import os.path
import re
import sys
from typing import Dict

import db

from handlers.admin import (
    HostApprovalHandler
)
from handlers.index import HealthHandler, MainHandler
from handlers.events import (
    EventHandler,
    EventImageHandler,
    RecommendedEventHandler,
    AcceptedEventHandler,
    AcceptEventHandler,
)
from handlers.login import (
    LoginHandler,
    LogoutHandler,
    HostSignupHandler,
    ReferralHandler,
    SignupHandler,
    TokenRequestHandler,
    TokenValidationHandler,
)
from handlers.notifications import (
    NotificationHandler,
    NotificationTokenHandler,
)
from handlers.user import (
    UserHandler,
    UserProfileHandler,
    UserPasswordHandler,
    UserPasswordResetHandler,
    UserPreferenceHandler,
    UserLocationHandler,
    UserSettingsHandler,
    UserVerificationHandler,
)
from handlers.admin import (
    UserReferralHandler,
    UserApprovedReferralHandler,
    UserPendingReferralHandler,
    # AdminHandler
)
from service.auth import JwtTokenService
from storage import ImageStore

from tornado import concurrent, httpserver, log, web
from tornado.ioloop import IOLoop
from tornado.options import define, options, parse_command_line


# options
define("config", default="./config.ini", type=str,
       help="Config file (default: ./config.ini)")
parse_command_line()
log.enable_pretty_logging()

class App(web.Application):
    """Wrapper around Tornado web application with configuration"""

    def __init__(
            self,
            debug: bool,
            token_service: JwtTokenService,
            image_store: ImageStore,
            static_path: str=None,
            **db_config: Dict[str, str]) -> None:
        """Initialize application

        debug: debug mode enabled
        static_path: path for static files
        db_config: database config
        """

        # async task executors
        thread_pool = concurrent.futures.ThreadPoolExecutor(4)

        # tornado web app
        endpoints = [
            # index
            (r"/(/*)", MainHandler),
            # server status
            (r"/health(/*)", HealthHandler),
            # login/token
            (r'/login(/*)', LoginHandler, dict(token_service=token_service)),
            (r'/token/request(/*)', TokenRequestHandler, dict(token_service=token_service)),
            (r'/token/validate(/*)', TokenValidationHandler, dict(token_service=token_service)),
            (r'/logout(/*)', LogoutHandler),
            (r'/signup(/*)', SignupHandler),
            (r'/signup/host(/*)', HostSignupHandler),
            # admin
            (r'/admin/approveHost(/*)', HostApprovalHandler),
            # users
            (r'/users(/*)', UserHandler),
            (r'/users/profile(/*)', UserProfileHandler),
            (r'/users/preferences(/*)', UserPreferenceHandler),
            (r'/users/settings(/*)', UserSettingsHandler),
            (r'/users/location(/*)', UserLocationHandler),
            (r'/users/verify(/*)', UserVerificationHandler),
            (r'/password', UserPasswordHandler),
            (r'/password/reset(/*)', UserPasswordResetHandler, dict(executor=thread_pool)),
            # events
            (r'/events(/*)', EventHandler, dict(executor=thread_pool)),
            (r'/events/(\d+/*)', EventHandler, dict(executor=thread_pool)),
            (r'/events/(\d+/*)/images(/*)', EventImageHandler, dict(image_store=image_store)),
            (r'/events/recommended(/*)', RecommendedEventHandler),
            (r'/events/accepted(/*)', AcceptedEventHandler),
            (r'/events/(\d+)/accept(/*)', AcceptEventHandler),
            # notifications
            (r'/notifications(/*)', NotificationHandler),
            (r'/token(/*)', NotificationTokenHandler),
            # TODO: finish these
            # (r'/signup/referral(/*)', ReferralHandler),     # sign-up with reference
            #(r'/referrals(/*)', UserReferralHandler),   # get user referrals
            #(r'/referrals/pending(/*)', UserPendingReferralHandler),    # get requested user referrals
            #(r'/referrals/approved(/*)', UserApprovedReferralHandler),  # get approved user referrals

            # OLD HANDLERS
            # (r'/users/admin(/*)', AdminHandler),            # make user admin
            # (r'/userfood(/*)', UserFoodPreferencesHandler)
            # (r'/events/new(/*)', EventTestHandler), # newest events
            # (r'/p(/*)', PreferenceHandler),
            # (r'/users/(\d+/*)', UserHandler),   # single user
            # (r'/users(/*)', UserHandler),       # all users
        ]

        # server settings
        settings = dict(static_path=static_path, debug=debug,)
        web.Application.__init__(self, endpoints, settings)

        # initialize database
        db.init(
            echo=debug,
            username=db_config['username'],
            password=db_config['password'],
            url=db_config['url'],
            database=db_config['database'],
            params=db_config['params'],
            generate=db_config['generate'])


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
    generate = db_config.getboolean('generate')
    if config.has_option('DB', 'options'):
        # convert options to url parameters
        params = '?' + re.sub(',\s*', '&', db_config.get('options'))
    else:
        params = ''

    # token service configuration
    token_service = JwtTokenService(server_config.get('secret'))
  
    # storage configuration
    store_config = config['STORE']
    image_store = ImageStore(store_config.get('images'))

    # logging configuration
    log_config = config['LOG']
    filename = log_config.get('file')
    level = log_config.get('level')
    fmt = log_config.get('format')
    logging.basicConfig(filename=filename, level=level, format=fmt)

    # create app
    app = App(
        debug=debug,
        token_service=token_service,
        image_store=image_store,
        username=username,
        password=password,
        url=url,
        database=database,
        params=params,
        generate=generate)

    # start server
    server = httpserver.HTTPServer(app)
    if procs == 1:
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
