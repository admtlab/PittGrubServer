"""
Send notifications to users
Author: Mark Silvis
"""

from typing import Any, Dict, Tuple, Union

from exponent_server_sdk import (
    PushClient, PushMessage, PushServerError, PushResponseError,
)


class InvalidExpoToken(Exception):
    def __init__(self):
        self.message = "Invalid expo token"
        super(self).__init__(self.message)


def send_push_to_users()

def send_push_notification(expo_token: str,
                           title: str,
                           body: str,
                           data: Dict[Any, Any]=None):
    """Send notification to specified expo token
    :expo_token: token to send notificaton to
    :title: notification title
    :body: notification body
    :data: extra notification data (total payload must be under 4096 bytes)
    :raises: ConnectionError, DeviceNotRegisterdError, HTTPError,
             InvalidExpoToken, PushServerError, PushResponseError
    """
    assert expo_token, "Expo token cannot be None"
    if PushClient().is_exponent_push_token(expo_token):
        message = PushMessage(to=expo_token, title=title, body=body, data=data)
        response = PushClient().publish(message)
        response.validate_response()
    else:
        raise InvalidExpoToken()
