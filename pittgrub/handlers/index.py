"""
Index handler
Author: Mark Silvis
"""


import logging
from datetime import datetime
import dateutil.parser
from copy import deepcopy
from db import User, FoodPreference, Event, EventFoodPreference, UserAcceptedEvent
from handlers.response import Payload, ErrorResponse
from handlers.base import BaseHandler
from requests.exceptions import ConnectionError, HTTPError
import json
import time
from util import json_esc

try:
    import tornado
except ModuleNotFoundError:
    # DB10 fix
    sys.path.insert(0, '/afs/cs.pitt.edu/projects/admt/web/sites/db10/beacons/python/site-packages/')
finally:
    from typing import Any, List, Dict
    from tornado import web, gen
    from tornado.escape import json_encode, json_decode
    from sqlalchemy.orm.exc import NoResultFound
    from exponent_server_sdk import PushClient, PushMessage, PushServerError, PushResponseError


def send_push_message(event: 'Event'):
    # notify users
    users = User.get_all()
    print(f'{len(users)} users')
    expo_tokens = [str(user.expo_token) for user in users]
    for token in expo_tokens:
        is_token = PushClient().is_exponent_push_token(token)
        print(f'is expo token: {is_token}')
        if not is_token:
            print(type(token) is str)
            print(token.startswith('ExponentPushToken'))
        else:
            try:
                message = PushMessage(to=token, body='New event!', data={'data': 'A new event was recently created'})
                response = PushClient().publish(message)
                response.validate_response()
            except PushServerError as e:
                print('Push server error\n')
                print(e)
                print('response')
                print(e.response)
                print(e.args)
                raise
            except (ConnectionError, HTTPError) as e:
                print('Connect error')
                print(e)
            except DeviceNotRegisteredError:
                # push token is not active
                # PushToken.bojects.filter
                print(f'inactive token for user {user.id}')
            except PushResponseError as e:
                print('per-notification error')
                print(e)


def send_notification(event: 'Event'):
    url = 'https://expo.host/--/api/v2/push/send'
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate",
        "Content-Type": "application/json"
    }
    payload = [{
        "badge": 1,        
        "sound": "default",
        "title": "New event",
        "body": f'{event.title} starts at {event.start_date}'
    }]

    for user in User.get_all():
        p = deepcopy(payload)
        p[0]['to'] = user.expo_token
        r = requests.post(url, data=json.dumps(payload), headers=headers)

    #messages = [PushMessage(to=token, body='New event!', data='New event created') for token in expo_tokens]
    #try:
    #    response = PushClient().publish_multiple(messages)
    #except PushServerError as e:
    #    print('Push server error\n')
    #    print(e)
    #    print(e.args)
    #except (ConnectionError, HTTPError) as e:
    #    print('Connect error')
    #    print(e)
    ## responses
    #if response is not None:
    #    print(f'response: {response}')
    #    try:
    #        response.validate_response()
    #    except DeviceNotRegisteredError:
    #        # push token is not active
    #        # PushToken.bojects.filter
    #        print(f'inactive token for user {user.id}')
    #    except PushResponseError as e:
    #        print('per-notification error')
    #        print(e)


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


class LoginHandler(BaseHandler):
    def post(self, path):
        data = json_decode(self.request.body)
        if User.verify(data['email'], data['password']):
            payload = dict({'user': User.get_by_email(data['email']).id})
            self.success(payload=payload)
        else:
            self.write_error(401, f'Incorrect email or password')


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


class NotificationTokenHandler(BaseHandler):
    def post(self, path):
        data = json_decode(self.request.body)
        if all(key in data for key in('user', 'token')):
            success = User.add_expo_token(data['user'], data['token'])
            if success:
                self.success()
            else:
                self.write_error(400, 'Error adding expo token')


class EventHandler(BaseHandler):
    def get(self, path):
        path = path.replace('/', '')

        # get data
        if path:
            value = Event.get_by_id(path)
        else:
            value = Event.get_all()

        # response
        if value is None:
            self.write_error(404, f'Event not found with id: {id}')
        else:
            self.set_status(200)
            payload = Payload(value)
            self.finish(payload)

    def post(self, path):
        # required json keys
        event_keys = ["title", "start_date", "end_date",
                      "address", "food_preferences"]
        # decode json
        data = json_decode(self.request.body)
        print(f'\ndata:\n{data}')
        # validate data
        if all(key in data for key in event_keys):
            data['start_date'] = dateutil.parser.parse(data['start_date'])
            data['start_date'] = data['start_date'].replace(tzinfo=None)
            data['end_date'] = dateutil.parser.parse(data['end_date'])
            data['end_date'] = data['end_date'].replace(tzinfo=None)                
            foodprefs = data.pop('food_preferences')
            # add event
            event = Event.add(**data)
            if event:
                # add food preferences
                EventFoodPreference.add(event.id, foodprefs)
                self.set_status(201)
                payload = Payload(event)
                self.success(201, payload)
                send_push_message(event)
                # send_notification(event)
            else:
                self.set_status(400)
                self.finish()
        else:
            # missing required field
            fields = ", ".join(set(event_keys)-data.keys())
            self.set_status(400)
            self.write(f'Error: missing field(s) {fields}')
            self.finish()


class RecommendedEventHandler(BaseHandler):
    
    def get(self, path):
        path = path.replace('/', '')

        # get data
        user = User.get_by_id(path)
        events = user.recommended_events
        self.set_status(200)
        payload = Payload(events)
        self.finish(payload)


class AcceptedEventHandler(BaseHandler):

    def get(self, path):
        path = path.replace('/', '')

        # get data
        user = User.get_by_id(path)
        events = user.accepted_events
        self.set_status(200)
        payload = Payload(events)
        self.finish(payload)


class AcceptEventHandler(BaseHandler):
    def post(self, event, user):
        UserAcceptedEvent.add(event, user)
        self.set_status(204)
        print(f'accepted event {event} for user {user}')
