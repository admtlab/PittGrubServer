from tornado.web import MissingArgumentError

from .response import Payload
from .base import BaseHandler
from db import User, UserActivation


class UserHandler(BaseHandler):
    def get(self, path):
        path = path.replace('/', '')
        # get data
        print('\n\nGOT PATH\n\n')
        if path:
            id = int(path)
            value = User.get_by_id(id)
        else:
            value = User.get_all()
        # response
        if value is None:
            self.write_error(404, f'User not found with id: {id}')
        else:
            self.set_status(200)
            payload = Payload(value)
            self.finish(payload)


class UserActivationHandler(BaseHandler):
    def get(self, path):
        try:
            id = self.get_query_argument('id')
            if User.activate(id):
                self.success(payload='Successfully verified account')
            else:
                self.write_error(404)
        except MissingArgumentError:
            self.write_error(404)
