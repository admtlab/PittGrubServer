"""
Index handler
Author: Mark Silvis
"""


import logging
from tornado import web, gen
from tornado.escape import json_encode
from sqlalchemy.orm.exc import NoResultFound
from db import Test, User, FoodPreference
from handlers.response import Payload, ErrorResponse
from handlers.base import BaseHandler
import json
import time
from util import json_esc


class MainHandler(web.RequestHandler):
    """Hello world request"""

    def get(self, path):
        logging.info("Sending new message")
        message = {
            'message': 'Hello, world!'
        }
        self.write(json_encode(message))
        self.finish()


class PreferenceHandler(web.RedirectHandler):
    def get(self, path):
        value = FoodPreference.get_all()
        if value is None:
            self.set_status(404)
            self.write("ERROR")
        else:
            self.set_status(200)
            self.write(Payload(value).json())
        self.finish()


class UserHandler(web.RequestHandler):
    def get(self, path):
        value = User.get_all()
        print(f'len of value: {len(value)}')
        if value is None:
            self.set_status(404)
            self.write("ERROR")
        else:
            print(f'\n\nuser id: {value[0].id}')
            print(f'user: {value[0]}')
            print(f'foodprefs: {value[0].foodpreftest}\n\n')
            print(f'vars: {vars(type(value[0]))}')
            print(f'\n\njson test: {value[0].json()}\n\n')
            # for pref in value[0].foodpreftest:
            #     print(pref.id)
            self.set_status(200)
            payload = Payload(value)
            print(f'TESTING PAYLOAD: {payload.json()}')
            self.write(Payload(value).json())
        self.finish()


# class UserFoodPreferencesHandler(web.RequestHandler):
#     def get(self, path):
#         value = UserFoodPreferences.get_all()
#         print(f'len of value: {len(value)}')
#         print(f'UserFoodPrefs: {value}')
#         if value is None:
#             self.set_status(404)
#             self.write("ERROR")
#         else:
#             self.set_status(200)
#             self.write(Payload(value).json())
#         self.finish()


class TestHandler(BaseHandler):
    """Test entity requests"""

    def get(self, path):
        print(f"Path is: {path}")
        print(f"\nself: href: {self.request.path}\n")
        value = Test.get_all()
        if value is None:
            self.set_status(404)
            self.write("ERROR")
        else:
            self.set_status(200)
            payload = Payload(value)
            print(json_esc(payload.prep()))
            self.write(Payload(value).json())
        self.finish()
        # value = yield gen.Task(Test.get_all)
        # try:
        #     if isinstance(value.result(), Exception):
        #         logging.warn("GOT EXCEPTION")                
        #         raise value.result()
        # except Exception as e:
        #     self.set_status(500)
        #     self.write("Internal server error")
        # else:
        #     if isinstance(value.result(), Test):
        #         self.set_status(200)
        #         self.write(payload(Tests=[i.dict() for i in value]))
        #     else:
        #         self.set_status(500)
        #         self.write("uh oh")
        # self.finish()
        # self.finish('{ "Tests": ' + str([i.dict() for i in value]) + ' }')
        # self.finish('{ "Tests": {} }'.format(value))
        # self.finish(json.dumps(value[0].dict()))
        # self.write(dict({'Tests': [i.dict() for i in value]}))
        # self.write(payload(Tests=[i.dict() for i in value]))


class TestHandlerId(BaseHandler):
    def get(self, id):
        value = Test.get_by_id(id)
        print(f"\nself: href: {self.request.path}\n")        
        if value is None:
            self.set_status(404)
            self.write(error(404, 'Not Found', f'Test not found with id {id}'))
        else:
            self.write(value.to_json())
        self.finish()

        # value = yield gen.Task(Test.get_by_id, int(id))
        # try:
        #     if isinstance(value.result(), Exception):
        #         logging.warn("GOT EXCEPTION")
        #         raise value.result()
        # except Exception as e:
        #     self.set_status(500)
        #     self.write("Internal server error")
        # else:
        #     if isinstance(value.result(), Test):
        #         self.set_status(200)
        #         self.write(value.result().to_json())
        #     else:
        #         self.set_status(500)
        #         self.write("uh oh")
        # self.finish()

    # @web.asynchronous
    # def get(self, id):
    #     value = yield gen.Task(Test.get_by_id, int(id))
    #     try:
    #         if isinstance(value.result(), Exception):
    #             raise value.result()
    #     except Exception as e:
    #         self.set_status(500)
    #         self.write("Internal server error")
    #     else:
    #         if isinstance(value.result(), Test):
    #             self.set_status(200)
    #             self.write(value.result().serialize())
    #     self.finish()


def payload(**kwargs):
    return dict({'_embedded': kwargs})


def error(status, error, message):
    timestamp = int(round(time.time()*1000))
    return dict({'timestamp': timestamp, 'status': status, 'error': error, 'message': message})
