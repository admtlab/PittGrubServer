"""
JSON reponses
Author: Mark Silvis
"""

import time
from typing import Any, Dict, List, Union
from util import json_dict, json_esc
import inflect
p = inflect.engine()


class Payload():
    """Response payload"""

    def __init__(self, response: Union[object, List[object]], **links: str):
        # response
        if isinstance(response, list):
            # generate response list
            if len(response):
                # list has items
                typ = type(response[0]).__name__
                name = p.plural(typ[0].lower()+typ[1:])
                objs = [res.json() for res in response]
                self._response = dict({name: objs})
            else:
                # empty list --> empty response
                self._response = dict()
        else:
            # generate response object
            assert response is not None
            self._response = response.json()
        # links
        if len(links) > 0:
            self._links = {'_links': {key.lower(): {'href': val} for key, val in links.items()}}
        else:
            self._links = None

    @property
    def response(self) -> Dict[str, Any]:
        """Get payload response"""
        return self._response

    @property
    def links(self) -> Dict[str, Dict[str, str]]:
        """Get payload links"""
        return self._links

    def add(rel: str, link: str) -> None:
        """Add link to payload
        Overwrites url if link already exists
        rel: relationship to response
        link: link to add
        """
        self._links['_links'][rel] = link

    def add(**links: str) -> None:
        """Add links to payload
        Overwrites url if link already exists
        rel: relationship to response
        link: link to add
        """
        for rel, link in links.items():
            self.add(rel, link)

    def prep(self) -> Dict[str, Any]:
        """Prepare payload for JSON serialization"""
        res = json_dict(self)
        # replace response with embedded keyword
        if 'response' in res:
            res['_embedded'] = res['response']
            del res['response']
            print(f'res: {res}')
        return res

    def json(self) -> str:
        """Returns escaped JSON encoding of payload"""
        return json_esc(self.prep())

    def json_test(self) -> str:
        j = dict()
        j['_embedded'] = self.response
        j['_links'] = self.links
        return json_esc(j)


class ErrorResponse():
    """Error response message"""

    def __init__(self, status: int, error: str, message: str=None):
        """
        status: HTTP status
        error:  HTTP error
        message: error message (default: None)
        """
        self.timestamp = int(round(time.time()*1000)) # ms
        self.status = status
        self.error = error
        self.message = message
