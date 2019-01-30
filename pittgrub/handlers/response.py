"""
JSON responses
Author: Mark Silvis
"""
import datetime
from http import HTTPStatus
from typing import Dict, List, Optional, Union
from util import json_esc

from domain.data import Data

import inflect


p = inflect.engine()


class Payload():
    """Response payload"""

    def __init__(self, response: Union[Data, List[Data]], **links: Dict[str, str]):
        # response
        assert response is not None, 'Response must not be None'
        self._response = response
        # links
        if len(links):
            self.add_links(links)
        else:
            self._links = None

    @property
    def response(self) -> Union[Data, List[Data]]:
        """Get payload response"""
        return self._response

    @property
    def links(self) -> Optional[Dict[str, str]]:
        """Get payload links"""
        return self._links

    def add_link(self, rel: str, link: str) -> None:
        """Add link to payload
        Overwrites link if href already exists
        rel: relationship to response
        link: link to add
        """
        if self._links is None:
            # links hasn't been created yet
            # create, then add link with rel
            self._links = {rel: link}
        else:
            self._links[rel] = link

    def add_links(self, **links) -> None:
        """Add links to payload
        Overwrites link if href already exists
        links: map of links, i.e. {rel: link}
        """
        if self._links is None:
            # links hasn't been created yet
            self._links = {key.lower(): {'href': val} for key, val in links.items()}
        else:
            self._links.update({key.lower(): {'href': val} for key, val in links.items()})

    def json(self) -> str:
        """Returns escaped JSON encoding of payload"""
        if isinstance(self._response, list):
            if len(self._response):
                if isinstance(self._response[0], Data):
                    typ = type(self._response[0]).__name__.replace("Data", "")
                else:
                    typ = type(self._response[0]).__name__
                name = p.plural(typ[0].lower()+typ[1:])
                embedded = dict({name: [res.json() for res in self._response]})
            else:
                embedded = dict()
            return json_esc(dict({
                    '_embedded': embedded,
                    '_links': self._links
                }))
        elif isinstance(self._response, Data):
            res = self._response.json()
            res['_links'] = self._links
            return json_esc(res)
        else:
            res['_links'] = self._links
            return json_esc(res)


class ErrorResponse():
    """Error response message"""

    def __init__(self, status: int, message: str=None):
        """
        status: HTTP status
        message: error message (default: None)
        """
        self.timestamp = datetime.datetime.now()
        self.status = status
        self.error = HTTPStatus(status).phrase
        self.message = message

    def json(self) -> str:
        err = dict({
            'timestamp': '{0:%Y-%m-%d %H:%M:%S}'.format(self.timestamp),
            'status': self.status,
            'error': self.error
        })
        if self.message:
            err['message'] = self.message
        return json_esc(err)
