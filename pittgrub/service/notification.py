"""
Send notifications to users
Author: Mark Silvis
"""

import logging
from requests import ConnectionError, HTTPError
from typing import Any, Dict, List, Union

from db import session_scope
from service.user import get_all_users

from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushResponseError,
    PushServerError,
)


class InvalidExpoToken(Exception):
    def __init__(self):
        self.message = "Invalid expo token"
        super(InvalidExpoToken,self).__init__(self.message)


def send_push_to_users(users: List['User'], title: str, body: str, data: Dict[Any, Any]=None) -> List[bool]:
    sent = [True] * len(users)
    for i, user in enumerate(users):
        if not user.expo_token:
            sent[i] = False
        else:
            notification_data = data or dict()
            notification_data['title'] = title
            notification_data['body'] = body
            notification_data['type'] = 'message'
            try:
                if send_push_notification(user.expo_token, title, body, notification_data):
                    sent[i] = True
                else:
                    sent[i] = False
            except Exception as e:
                logging.error(e)
                sent[i] = False
    return sent

#Is this right?
def send_to_all_users(title: str, body: str, data: Dict[Any, Any]=None) -> List[bool]:
    return send_push_to_users(get_all_users())


def send_push_notification(expo_token: str,
                           title: str,
                           body: str,
                           data: Dict[Any, Any]=None) -> bool:
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
        try:
            message = PushMessage(to=expo_token, title=title, body=body, data=data)
            response = PushClient().publish(message)
            response.validate_response()
            return True
        except PushServerError as e:
            logging.error(f"Push Server Error\n{e}")
            logging.error(f"Response\n{e.response}")
            logging.error(f"Args\n{e.args}")
        except (ConnectionError, HTTPError) as e:
            logging.error(f"Connection/HTTPError\n{e}")
        except DeviceNotRegisteredError as e:
            logging.warning(f'Inactive token\n{e}')
        except PushResponseError as e:
            logging.error(f'Notification error\n{e}')
        return False
    else:
        raise InvalidExpoToken()
