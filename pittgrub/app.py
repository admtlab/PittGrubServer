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
# index: Main, Health, Test
# login: Login, Logout, Signup, Referrals
# tokens: token handling
# users: Users/Verification/Preference/Settings
# notifiations: all notifications
# events: all event stuff

from handlers.admin import (
    HostApprovalHandler
)
from handlers.index import (
    HealthHandler,
    MainHandler,
    TestHandler
)
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
    TokenRefreshHandler,
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

    def __init__(self, debug: bool, image_store: ImageStore, static_path: str=None, **db_config: Dict[str, str]) -> None:
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
            (r"/(/*)",          MainHandler),       # index/welcome
            (r"/health(/*)",    HealthHandler),     # server status
            (r"/test(/*)",      TestHandler),       # testing
            # login
            (r'/login(/*)',             LoginHandler),              # log-in with credentials
            (r'/login/refresh(/*)',     TokenRefreshHandler),       # refresh token
            (r'/login/validate(/*)',    TokenValidationHandler),    # validate token
            (r'/logout(/*)',            LogoutHandler),             # delete access token
            (r'/signup(/*)',            SignupHandler),             # sign-up
            (r'/signup/host(/*)',       HostSignupHandler),         # sign-up with host access request
            # admin
            (r'/admin/approveHost(/*)', HostApprovalHandler),   # approve request for host access
            # user
            (r'/users/verify(/*)', UserVerificationHandler),    # user activation
            (r'/users/profile(/*)', UserProfileHandler),
            (r'/users/preferences(/*)', UserPreferenceHandler), # user preferences (food, etc)
            (r'/users/settings(/*)', UserSettingsHandler),      # user settings (food preferences, pantry, etc)
            (r'/users/location(/*)', UserLocationHandler),
            (r'/password', UserPasswordHandler),                # Change user password
            (r'/password/reset(/*)', UserPasswordResetHandler,
                dict(executor=thread_pool)),                    # Reset user's password
            # notifications
            (r'/notifications(/*)', NotificationHandler),   # handle notifications
            (r'/token(/*)', NotificationTokenHandler),      # add notification token
            # events
            (r'/events(/*)', EventHandler,
                dict(executor=thread_pool)),                    # all events
            (r'/events/(\d+/*)', EventHandler,
                dict(executor=thread_pool)),                    # single event
            (r'/events/(\d+/*)/images(/*)', EventImageHandler,
                dict(image_store=image_store)),                 # event images
            (r'/events/recommended/(\d+/*)', RecommendedEventHandler),  # recommended events for a user
            (r'/events/accepted/(\d+/*)', AcceptedEventHandler),        # accepted events for a user
            (r'/events/(\d+)/accept/(\d+/*)', AcceptEventHandler),      # accept an event for a user
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
        settings = dict(
            static_path=static_path,
            debug=debug,)
        web.Application.__init__(self, endpoints, settings)

        # initialize database
        db.init(username=db_config['username'], password=db_config['password'],
                url=db_config['url'], database=db_config['database'],
                params=db_config['params'], echo=debug, generate=db_config['generate'])


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
    app = App(debug, image_store=image_store, username=username, password=password,
              url=url, database=database, params=params, generate=generate)

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
