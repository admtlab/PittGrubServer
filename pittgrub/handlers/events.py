"""
Handler for event endpoints
Author: Mark Silvis
"""

from io import BytesIO

from PIL import Image

from db import Event, EventImage
from handlers.response import Payload
from handlers import BaseHandler, SecureHandler
from storage import ImageStore


class EventTestHandler(BaseHandler):
    def get(self, path):
        events = Event.get_all_newest()
        self.success(status=200, payload=Payload(events))


class EventImageHandler(BaseHandler):

    def initialize(self, image_store: ImageStore):
        self.image_store = image_store

    def get(self, event_id, path):
        event = Event.get_by_id(event_id)
        if event is None:
            self.write_error(404, f'Event not found with id: {id}')
        else:
            event_image = EventImage.get_by_event(event_id)
            if event_image is None:
                self.success(status=404, 'Event does not have an image')
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
        #requester = self.get_jwt()['own']
        event = Event.get_by_id(event_id)
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
                event_image = EventImage.add(event_id)
                image_id = event_image.id
                if self.image_store.save_image(image_id, image):
                    self.success(status=201, payload=dict(image=self.image_store.get_name(image_id)))
                else:
                    self.write_error(400, f'Failed to upload image')
