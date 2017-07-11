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
import db
from handlers.index import *

# dependencies
try:
    import tornado
except ModuleNotFoundError:
    # DB10 fix
    sys.path.insert(0, '/afs/cs.pitt.edu/projects/admt/web/sites/db10/beacons/python/site-packages/')
finally:
    from tornado import httpserver, log, web
    from tornado.ioloop import IOLoop
    from tornado.options import options, define, parse_command_line
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker


# options
define("config", default="./config.ini", type=str,
       help="Config file (default: ./config.ini)")
# define("port", default=8080, help="app port", type=int)
# define("procs", default=1, help="number of processes (0 = # CPUs)")
# define("debug", default=True, help="debug mode")
# define("autoreload", default=True, help="autoreload setting")
parse_command_line()
log.enable_pretty_logging()


class App(web.Application):
    """Wrapper around Tornado web application with configuration"""

    def __init__(self, debug: bool, **db_config: Dict[str, str]):
        """Initialize application

        debug: debug mode enabled
        db_config: database config
        """
        # tornado web app
        handlers = [
            (r"/(/*)", MainHandler),            # index
            (r'/test(/*)', TestHandler),
            (r'/test/([0-9]+)', TestHandlerId),
            (r'/user(/*)', UserHandler),        # all users
            (r'/user/(\d+/*)', UserHandler),    # single user
            (r'/p(/*)', PreferenceHandler),
            (r'/event(/*)', EventHandler),      # all events
            (r'/event/(\d+/*)', EventHandler),  # single event
            # (r'/userfood(/*)', UserFoodPreferencesHandler)
        ]
        settings = dict(
            debug=debug,
            autoreload=debug,
        )
        web.Application.__init__(self, handlers, **settings)

        # init database engine and session
        engine = create_engine(f"mysql+pymysql://{db_config['username']}:{db_config['password']}@{db_config['url']}/{db_config['database']}{db_config['params']}", convert_unicode=True, echo=debug)
        db.init(engine, debug)
        self.db = scoped_session(sessionmaker(bind=engine))


def main():
    """Make application"""

    # get configuration file
    if not os.path.isfile(options.config):
        sys.exit("Error: config file not found")
    config = configparser.ConfigParser()
    config.read(options.config)
    print(f'type: {type(config)}')

    # server configuration
    server_config = config['SERVER']
    port = server_config['port']
    procs = server_config['procs']
    debug = server_config.getboolean('debug')
    if config.has_option('SERVER', 'autoreload'):
        autoreload = server_config.getboolean('autoreload')
    else:
        autoreload = debug

    # database configuration
    db_config = config['DB']
    username = db_config['username']
    password = db_config['password']
    url = db_config['url']
    database = db_config['database']
    if config.has_option('DB', 'options'):
        # convert options to url parameters
        params = '?' + re.sub(',\s*', '&', db_config['options'])
    else:
        params = ''

    # logging configuration
    log_config = config['LOG']
    filename = log_config['file']
    level = log_config['level']
    fmt = log_config['format']
    logging.basicConfig(filename=filename, level=level, format=fmt)

    # start server
    if (procs == 1):
        # single process
        server = httpserver.HTTPServer(
            App(debug, username=username, password=password, url=url, database=database, params=params))
        server.listen(port)
        server.start()
        IOLoop.current().start()
    else:
        # multiple processes
        server = httpserver.HTTPServer(
            App(debug, username=username, password=password, url=url, database=database, params=params))
        server.bind(port)
        server.start(procs)
        IOLoop.current().start()


if __name__ == '__main__':
    sys.exit(main())
