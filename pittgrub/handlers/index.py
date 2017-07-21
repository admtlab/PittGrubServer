"""
Index handler
Author: Mark Silvis
"""


import logging
from datetime import datetime
from typing import Any, List, Dict
from tornado import web, gen
from tornado.escape import json_encode, json_decode
from sqlalchemy.orm.exc import NoResultFound
from db import Test, User, FoodPreference, Event
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


class PreferenceHandler(web.RequestHandler):
    def get(self, path):
        value = FoodPreference.get_all()
        if value is None:
            self.set_status(404)
            self.write("ERROR")
        else:
            self.set_status(200)
            self.write(Payload(value).json())
        self.finish()


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

class EventHandler(BaseHandler):
    def get(self, path):
        time.sleep(1)
        path = path.replace('/', '')
        # get data
        if path:
            id = int(path)
            value = Event.get_by_id(id)
        else:
            value = Event.get_all()
        # response
            if value is None:
                self.write_error(400, f'Event not found with id: {id}')
            else:
                self.set_status(200)
                payload = Payload(value)
                self.finish(payload)
    
    def post(self, path):
        # title = self.get_argument('title')
        # start_date = datetime.strptime(self.get_argument('start_date'))
        # end_date = datetime.strptime(self.get_argument('end_date'))
        # details = self.get_argument('details')
        # servings = self.get_argument('servings')
        # address = self.get_argument('address')
        # location = self.get_argument('location')
        data = json_decode(self.request.body)
        print('data: ', data)
        title = data['title']
        # start_date = datetime.strptime(data['start_date'], '%y-%m-%d %H:%M:%S')
        # end_date = datetime.strptime(data['end_date'], '%y-%m-%d %H:%M:%S')
        details = data['details']
        servings = data['servings']
        address = data['address']
        location = data['location']
        event = Event.add(title, datetime.now(), datetime.now(), details, servings, address, location)
        self.set_status(201)
        payload = Payload(event)
        self.finish(payload)


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
        print('request: ', self.request)
        print(f"\nself: href: {self.request.uri}\n")
        value = Test.get_all()
        if value is None:
            self.set_status(404)
            self.write("ERROR")
        else:
            print('writing payload')
            self.set_status(200)
            payload = Payload(value)
            self.write(payload)
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
