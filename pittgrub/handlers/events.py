"""
Handler for event endpoints
Author: Mark Silvis
"""

import logging
from io import BytesIO

import dateutil
from PIL import Image

from handlers import SecureHandler
from handlers.response import Payload
from service.auth import JwtTokenService
from service.event import (
    add_event_image,
    create_event,
    get_event,
    get_event_by_user,
    get_event_image_by_event,
    get_active,
    get_active_by_user,
    set_food_preferences,
    user_accept_event,
    user_accepted_events,
    user_recommended_events_valid,
)
from service.notification import send_push_to_users
from service.recommender import _event_recommendation
from storage import ImageStore


class EventHandler(SecureHandler):
    required_fields = set(["title", "start_date", "end_date", "address", "servings", "food_preferences", "latitude", "longitude"])

    def initialize(self, token_service: JwtTokenService, executor: 'ThreadPoolExecutor'):
        super().initialize(token_service)
        self.executor = executor

    def get(self, path):
        path = path.replace('/', '')

        if path:
            # get single event
            if not (isinstance(path, int) or path.isdecimal()):
                self.write_error(400, f'Error: Invalid event id')
            else:
                value = get_event_by_user(int(path), self.get_user_id())
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
            value = get_active_by_user(self.get_user_id())
            payload = Payload(value)
            self.success(200, payload)
            self.finish()

    def post(self, path):
        if not self.has_host_role():
            self.write_error(400, 'Error: insufficient permissions')
        else:
            # decode json
            data = self.get_data()
            # validate data
            data['start_date'] = dateutil.parser.parse(data['start_date'])
            data['start_date'] = data['start_date'].replace(tzinfo=None)
            data['end_date'] = dateutil.parser.parse(data['end_date'])
            data['end_date'] = data['end_date'].replace(tzinfo=None)
            data['organizer'] = self.get_user_id()
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


class RecommendedEventHandler(SecureHandler):

    def get(self, path):
        user_id = self.get_user_id()
        events = user_recommended_events_valid(user_id)
        self.success(200, Payload(events))
        self.finish()


class AcceptedEventHandler(SecureHandler):

    def get(self, path):
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
        self.finish()
        logging.info(f'accepted event {event} for user {user_id}')


class EventImageHandler(SecureHandler):

    def initialize(self, token_service: JwtTokenService, image_store: ImageStore):
        super().initialize(token_service)
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
        self.finish()

    def post(self, event_id, path):
        event = get_event(event_id)
        if event is None:
            self.write_error(404, f'Event not found with id: {id}')
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
        self.finish()
