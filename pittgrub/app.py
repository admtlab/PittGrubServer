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
define("config", default="./config.ini", type=str, help="config file")
define("port", default=8080, help="app port", type=int)
define("procs", default=1, help="number of processes (0 = # CPUs)")
define("debug", default=True, help="debug mode")
define("autoreload", default=True, help="autoreload setting")
parse_command_line()
log.enable_pretty_logging()


class App(web.Application):
    """Wrapper around Tornado web application with configuration"""

    def __init__(self, config):
        """Initialize application
        config: db configuration
        """
        print(f"type of config: {type(config)}")
        # tornado web app
        handlers = [
            (r"/(/*)", MainHandler),
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
            debug=options.debug,
            autoreload=options.autoreload,
        )
        web.Application.__init__(self, handlers, **settings)

        # database config
        db_config = config['DB']
        server = db_config['server']
        driver = db_config['driver']
        user = db_config['username']
        password = db_config['password']
        url = db_config['url']
        database = db_config['database']
        params = '?'+re.sub(',\s*', '&', db_config['options']) if db_config['options'] else ''

        # init database engine and session
        engine = create_engine(f"{server}+{driver}://{user}:{password}@{url}/{database}{params}", convert_unicode=True, echo=options.debug)
        db.init(engine, options.debug)
        self.db = scoped_session(sessionmaker(bind=engine))


def main():
    """Make application"""

    # get configuration
    if not os.path.isfile(options.config):
        sys.exit("Error: config file not found")
    config = configparser.ConfigParser()
    config.read(options.config)

    # logging configuration
    log_config = config['LOG']
    filename = log_config['file']
    level = log_config['level']
    format = log_config['format']
    logging.basicConfig(filename=filename,
                        level=level,
                        format=format)

    # start server
    if (options.procs == 1):
        # single process
        server = httpserver.HTTPServer(App(config))
        server.listen(options.port)
        server.start()
        IOLoop.current().start()
    else:
        # multiple processes
        server = httpserver.HTTPServer(App(config))
        server.bind(options.port)
        server.start(options.procs)
        IOLoop.current().start()


if __name__ == '__main__':
    sys.exit(main())
