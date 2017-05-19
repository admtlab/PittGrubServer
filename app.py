"""
PittGrub Server
Author: Mark Silvis
Author: David Tsui
"""

# python
import configparser
import os.path
import re
import sys

# modules
import db
from handlers.index import MainHandler, TestHandler, TestHandlerId

# dependencies
try:
    import tornado
except ModuleNotFoundError:
    # DB10 fix
    sys.path.insert(0, '/afs/cs.pitt.edu/projects/admt/web/sites/db10/beacons/python/site-packages/')
finally:
    from tornado import httpserver, web
    from tornado.ioloop import IOLoop
    from tornado.options import options, define, parse_command_line
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker


# options
define("config", default="./config", type=str, help="config file")
define("port", default=8080, help="app port", type=int)
define("procs", default=1, help="number of processes (0 = # CPUs)")
define("debug", default=True, help="debug mode")
define("autoreload", default=True, help="autoreload setting")
parse_command_line()


class App(web.Application):
    """Wrapper around Tornado web application with configuration"""

    def __init__(self, config):
        # tornado web app
        handlers = [
            (r"/(/*)", MainHandler),
            (r'/test(/*)', TestHandler),
            (r'/test/([0-9]+)', TestHandlerId),
        ]
        settings = dict(
            debug=options.debug,
            autoreload=options.autoreload,
        )
        web.Application.__init__(self, handlers, **settings)

        # database config
        config.read(options.config)
        db_config = config['DB']
        database = db_config['database']
        driver = db_config['driver']
        user = db_config['username']
        password = db_config['password']
        url = db_config['url']
        name = db_config['name']
        params = '?'+re.sub(',\s*', '&', db_config['options']) if db_config['options'] else ''

        # init database engine and session
        engine = create_engine(f"{database}+{driver}://{user}:{password}@{url}/{name}{params}", convert_unicode=True, echo=options.debug)
        db.init(engine, options.debug)
        self.db = scoped_session(sessionmaker(bind=engine))


def main():
    """Make application"""

    # get configuration
    if not os.path.isfile(options.config):
        sys.exit("Error: config file not found")
    config = configparser.ConfigParser()

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
