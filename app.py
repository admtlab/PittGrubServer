"""
PittGrub Server
Author: Mark Silvis
Author: David Tsui
"""

import sys
try:
    import tornado
except ModuleNotFoundError:
    # DB10 fix
    sys.path.insert(0, '/afs/cs.pitt.edu/projects/admt/web/sites/db10/beacons/python/site-packages/')
finally:
    from tornado import httpserver, web
    from tornado.ioloop import IOLoop
    from tornado.options import options, define, parse_command_line
from handlers.index import MainHandler


# options
define("port", default=8080, help="app port", type=int)
define("procs", default=1, help="number of processes (0 = # CPUs)")
define("debug", default=True, help="debug mode")
define("autoreload", default=True, help="autoreload setting")


def main():
    """Make application"""
    # get options
    parse_command_line()

    # make app
    app = web.Application([
        (r"/", MainHandler),
    ],
    debug=options.debug,
    autoreload=options.autoreload)

    # start server
    if (options.procs == 1):
        # single process
        server = httpserver.HTTPServer(app)
        server.listen(options.port)
        server.start()
        IOLoop.current().start()
    else:
        # multiple processes
        server = httpserver.HTTPServer(app)
        server.bind(options.port)
        server.start(options.procs)
        IOLoop.current().start()


if __name__ == '__main__':
    sys.exit(main())
