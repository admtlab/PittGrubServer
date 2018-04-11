"""
Handler for event endpoints
Author: Mark Silvis
"""

import logging
from datetime import datetime
from io import BytesIO

from db import Event, EventImage
from handlers.response import Payload
from handlers import BaseHandler, SecureHandler
from service.event import (
    add_event_image,
    create_event,
    get_event,
    get_events,
    get_event_image_by_event,
    get_newest,
    set_food_preferences,
    user_accept_event,
    user_accepted_events,
    user_recommended_events,
    user_recommended_events_valid,
)
from service.user import get_user
from service.notification import send_push_to_users
from service.recommender import _event_recommendation
from storage import ImageStore

import dateutil
from exponent_server_sdk import (
    PushClient, PushMessage, PushResponseError, PushServerError, DeviceNotRegisteredError
)
from PIL import Image

class EventTestHandler(BaseHandler):
    def get(self, path):
        events = Event.get_all_newest()
        self.success(status=200, payload=Payload(events))


# def send_push_notification(user: 'User', event: 'Event'):
#     expo_token = user.expo_token
#     if expo_token:
#         if PushClient().is_exponent_push_token(expo_token):
#             try:
#                 message = PushMessage(to=expo_token,
#                                       title='PittGrub: New event!',
#                                       body=event.title,
#                                       data={'type': 'event', 'event': event.title, 'title':'PittGrub: New event!', 'body': event.title})
#                 response = PushClient().publish(message)
#                 response.validate_response()
#             except PushServerError as e:
#                 print('push server error')
#                 print(e)
#                 print(f'Response: {e.response}')
#                 print(f'Args: {e.args}')
#             except (ConnectionError, HTTPError) as e:
#                 print('Connection/HTTP error')
#                 print(e)
#             except DeviceNotRegisteredError as e:
#                 print(f'Inactive token for user: {user.id}')
#             except PushResponseError as e:
#                 print('notification error')
#                 print(e)
#
#
# def send_push_message(event: 'Event'):
#     # notify users
#     users = User.get_all()
#     print(f'{len(users)} users')
#     expo_tokens = [str(user.expo_token) for user in users]
#     for token in expo_tokens:
#         is_token = PushClient().is_exponent_push_token(token)
#         print(f'is expo token: {is_token}')
#         if not is_token:
#             print(type(token) is str)
#             print(token.startswith('ExponentPushToken'))
#         else:
#             try:
#                 message = PushMessage(to=token, body='New event!', data={'data': 'A new event was recently created'})
#                 response = PushClient().publish(message)
#                 response.validate_response()
#             except PushServerError as e:
#                 print('Push server error\n')
#                 print(e)
#                 print('response')
#                 print(e.response)
#                 print(e.args)
#                 raise
#             except (ConnectionError, HTTPError) as e:
#                 print('Connect error')
#                 print(e)
#             except DeviceNotRegisteredError:
#                 # push token is not active
#                 # PushToken.bojects.filter
#                 print(f'inactive token for user {user.id}')
#             except PushResponseError as e:
#                 print('per-notification error')
#                 print(e)
#
#
# def send_notification(event: 'Event'):
#     url = 'https://expo.host/--/api/v2/push/send'
#     headers = {
#         "Accept": "application/json",
#         "Accept-Encoding": "gzip, deflate",
#         "Content-Type": "application/json"
#     }
#     payload = [{
#         "badge": 1,
#         "sound": "default",
#         "title": "New event",
#         "body": f'{event.title} starts at {event.start_date}'
#     }]
#
#     for user in User.get_all():
#         p = deepcopy(payload)
#         p[0]['to'] = user.expo_token
#         r = requests.post(url, data=json.dumps(payload), headers=headers)

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


class EventHandler(BaseHandler):

    def initialize(self, executor: 'ThreadPoolExecutor'):
        self.executor = executor

    def get(self, path):
        path = path.replace('/', '')

        if path:
            # get single event
            if not (isinstance(path, int) or path.isdecimal()):
                self.write_error(400, f'Error: Invalid event id')
            else:
                value = get_event(int(path))
                if value is None:
                    # event not found
                    self.write_error(404, f'Event not found with id: {path}')
                else:
                    # event found
                    self.set_status(200)
                    payload = Payload(value)
                    event_image = get_event_image_by_event(value.id)
                    # attach image link if available
                    if event_image is not None:
                        payload.add("image", f"/events/{path}/images")
                    # send response
                    self.finish(payload)
        else:
            # get event list
            value = get_newest()
            self.set_status(200)
            payload = Payload(value)
            self.finish(payload)

    def post(self, path):
        # required json keys
        event_keys = ["title", "start_date", "end_date",
                      "address", "food_preferences"]
        # decode json
        data = self.get_data()
        # validate data
        if all(key in data for key in event_keys):
            data['start_date'] = dateutil.parser.parse(data['start_date'])
            data['start_date'] = data['start_date'].replace(tzinfo=None)
            data['end_date'] = dateutil.parser.parse(data['end_date'])
            data['end_date'] = data['end_date'].replace(tzinfo=None)
            foodprefs = data.pop('food_preferences')
            # add event
            event = create_event(**data)
            if event:
                # add food preferences
                set_food_preferences(event.id, foodprefs)
                payload = Payload(event)
                self.success(201, payload)
                # asynchronously send notification to recommend users
                self.executor.submit(
                    send_push_to_users,
                    _event_recommendation(event),
                    'PittGrub: New Event!',
                    event.title,
                    data={
                        'type': 'event',
                        'event': event.title,
                        'title':'PittGrub: New event!',
                        'body': event.title})
            else:
                self.set_status(400)
                self.finish()
        else:
            # missing required field
            fields = ", ".join(set(event_keys)-data.keys())
            self.set_status(400)
            self.write(f'Error: missing field(s) {fields}')
            self.finish()


class RecommendedEventHandler(SecureHandler):

    def get(self, path):
        path = path.replace('/', '')
        user_id = self.get_user_id()
        events = user_recommended_events_valid(user_id)
        self.success(200, Payload(events))
        self.finish()


class AcceptedEventHandler(SecureHandler):

    def get(self, path):
        path = path.replace('/', '')

        # get data
        user_id = self.get_user_id()
        events = user_accepted_events(user_id)
        self.success(200, Payload(events))
        self.finish()


class AcceptEventHandler(SecureHandler):
    def post(self, event):
        user_id = self.get_user_id()
        user_accept_event(event, user_id)
        self.set_status(204)
        logging.info(f'accepted event {event} for user {user_id}')


class EventImageHandler(BaseHandler):

    def initialize(self, image_store: ImageStore):
        self.image_store = image_store

    def get(self, event_id, path):
        event_image = get_event_image_by_event(event_id)
        if event_image is None:
            self.write_error(404, f'Event image not found for event {event_id}')
        else:
            image = self.image_store.fetch_image(event_image.id)
            if image is None:
                self.write_error(400, 'Error reading image')
            else:
                out = BytesIO()
                image.save(out, format="JPEG")
                stream = out.getvalue()
                self.set_header("Content-Type", "image/jpeg")
                self.set_header("Content-Length", len(stream))
                self.write(stream)

    def post(self, event_id, path):
        event = get_event(event_id)
        if event is None:
            self.write_error(404, f'Event not found with id: {id}')
        #elif not requester == event.organizer_id:
        #    self.write_error(403, 'Only the event organizer can upload images')
        else:
            image = self.request.files['image'][0]
            if image is None:
                self.write_error(400, 'Missing image file')
            else:
                image = Image.open(BytesIO(image['body']))
                event_image = add_event_image(event_id)
                image_id = event_image.id
                if self.image_store.save_image(image_id, image):
                    self.success(status=201, payload=dict(image=self.image_store.get_name(image_id)))
                else:
                    self.write_error(400, f'Failed to upload image')
