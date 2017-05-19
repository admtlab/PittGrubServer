"""
JSON reponses
Author: Mark Silvis
"""

import time
from typing import Any, Dict, List, Union
from util import property_dict
import inflect
p = inflect.engine()


class Payload():
    """Response payload"""

    def __init__(self, response: Union[object, List[object]], **links: str):
        # response
        if isinstance(response, list):
            # generate response list
            assert len(response) > 0
            typ = type(response[0]).__name__
            name = p.plural(typ[0].lower()+typ[1:])
            objs = [property_dict(res) for res in response]
            self._response = dict({name: objs})
        else:
            # generate response object
            assert response is not None
            self._response = property_dict(response)
        # links
        if len(links) > 0:
            self._links = {'_links': {key.lower(): {'href': val} for key, val in links.items()}}

    @property
    def response(self) -> Dict[str, Any]:
        """Get payload response"""
        return self._response

    @property
    def links(self) -> Dict[str, Dict[str, str]]:
        """Get payload links"""
        return self._links

    def prep(self) -> Dict[str, Any]:
        """Prepare payload for json serialization"""
        return property_dict(self)

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


class ErrorMessage():
    """Error response"""

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
