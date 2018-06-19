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

from tornado import concurrent, httpserver, log, web
from tornado.ioloop import IOLoop
from tornado.options import define, options, parse_command_line

import db
from handlers.admin import HostApprovalHandler
from handlers.events import (AcceptedEventHandler, AcceptEventHandler,
                             EventHandler, EventImageHandler,
                             RecommendedEventHandler)
from handlers.index import EmailListAddHandler, EmailListRemoveHandler, HealthHandler, MainHandler
from handlers.login import (HostSignupHandler, LoginHandler, LogoutHandler,
                            SignupHandler)
from handlers.notifications import NotificationHandler
from handlers.token import (NotificationTokenHandler, TokenRequestHandler,
                            TokenValidationHandler)
from handlers.user import (UserHandler, UserLocationHandler,
                           UserPasswordHandler, UserPasswordResetHandler,
                           UserProfileHandler, UserVerificationHandler)
from service.auth import JwtTokenService
from storage import ImageStore


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
            # email list
            (r'/email/add(/*)', EmailListAddHandler),
            (r'/email/remove(/*)', EmailListRemoveHandler),
            # login/singup
            (r'/login(/*)', LoginHandler, dict(token_service=token_service)),
            (r'/logout(/*)', LogoutHandler, dict(token_service=token_service)),
            (r'/signup(/*)', SignupHandler, dict(token_service=token_service)),
            (r'/signup/host(/*)', HostSignupHandler, dict(token_service=token_service)),
            # token
            (r'/token/request(/*)', TokenRequestHandler, dict(token_service=token_service)),
            (r'/token/validate(/*)', TokenValidationHandler, dict(token_service=token_service)),
            (r'/token/notification(/*)', NotificationTokenHandler, dict(token_service=token_service)),
            # admin
            (r'/admin/approveHost(/*)', HostApprovalHandler, dict(token_service=token_service)),
            # users
            (r'/users(/*)', UserHandler, dict(token_service=token_service)),
            (r'/users/profile(/*)', UserProfileHandler, dict(token_service=token_service)),
            (r'/users/location(/*)', UserLocationHandler, dict(token_service=token_service)),
            (r'/users/verify(/*)', UserVerificationHandler, dict(token_service=token_service)),
            (r'/users/password', UserPasswordHandler, dict(token_service=token_service)),
            (r'/users/password/reset(/*)', UserPasswordResetHandler, dict(token_service=token_service, executor=thread_pool)),
            # events
            (r'/events(/*)', EventHandler, dict(token_service=token_service, executor=thread_pool)),
            (r'/events/(\d+/*)', EventHandler, dict(token_service=token_service, executor=thread_pool)),
            (r'/events/(\d+/*)/images(/*)', EventImageHandler, dict(token_service=token_service, image_store=image_store)),
            (r'/events/recommended(/*)', RecommendedEventHandler, dict(token_service=token_service)),
            (r'/events/accepted(/*)', AcceptedEventHandler, dict(token_service=token_service)),
            (r'/events/accept(/*)', AcceptEventHandler, dict(token_service=token_service)),
            # notifications
            (r'/notifications(/*)', NotificationHandler, dict(token_service=token_service)),
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
