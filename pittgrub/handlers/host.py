import json
from handlers.base import BaseHandler
from handlers.response import Payload
from util import json_esc


class HostTrainingSlidesHandler(BaseHandler):
    host_training_data = [
        {
            "title": "Title",
            "subtitle": "Be sure to do this!",
            "image": "https://google.com"
        }, {
            "title": "Another Slide",
            "subtitle": "Be sure to do this, too! And visit [Google](https://google.com)!",
            "image": "https://google.com"
        }, {
            "title": "Last Slide",
            "subtitle": "Here is a long line of text with a link starting here: [Google is cool](http://google.com). There is some more text and another link coming soon...not yet........surprise [laldjfjdsalkf fjdslafdas](http://blah.com). This should not match btw [fjkdsafsd](http:/not-a-domain.com)",
            "image": "https://google.com"
        }
    ]

    def get(self, path):
        self.success(payload=json_esc(self.host_training_data))
