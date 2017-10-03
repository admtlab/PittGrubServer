"""
JSON reponses
Author: Mark Silvis
"""

import time
from typing import Any, Dict, List, Optional, Union
from util import json_dict, json_esc
from db import Entity
from http import HTTPStatus
from sqlalchemy.ext.associationproxy import _AssociationList
import datetime
import inflect
p = inflect.engine()


class Payload():
    """Response payload"""

    def __init__(self, response: Union[Entity, List[Entity]], **links: str):
        # response
        assert response is not None, 'Response must not be None'
        self._response = response
        # links
        if len(links):
            self._links = {key.lower(): {'href': val} for key, val in links.items()}
        else:
            self._links = None

    @property
    def response(self) -> Union[Entity, List[Entity]]:
        """Get payload response"""
        return self._response

    @property
    def links(self) -> Optional[Dict[str, str]]:
        """Get payload links"""
        return self._links

    def add(self, rel: str, link: str) -> None:
        """Add link to payload
        Overwrites url if link already exists
        rel: relationship to response
        link: link to add
        """
        if self._links is None:
            # links hasn't been created yet
            # create, then add link with rel
            self._links = {rel: link}
        else:
            self._links[rel] = link

   # def add(self, **links: str) -> None:
   #     """Add links to payload
   #     Overwrites url if link already exists
   #     rel: relationship to response
   #     link: link to add
   #     """
   #     for rel, link in links.items():
   #         self.add(rel, link)

    def json(self, deep: bool=False) -> str:
        """Returns escaped JSON encoding of payload"""
        if isinstance(self._response, (list, _AssociationList)):
            if len(self._response):
                typ = type(self._response[0]).__name__
                name = p.plural(typ[0].lower()+typ[1:])
                embedded = dict({name: [res.json(deep) for res in self._response]})
            else:
                embedded = dict()
            return json_esc(dict({
                    '_embedded': embedded,
                    '_links': self._links
                }))
        else:
            res = self._response.json(deep)
            res['_links'] = self._links
            return json_esc(res)


class ErrorResponse():
    """Error response message"""

    def __init__(self, status: int, message: str=None):
        """
        status: HTTP status
        message: error message (default: None)
        """
        # self.timestamp = int(round(time.time()*1000)) # ms
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
