import configparser
from datetime import datetime, timedelta
from typing import Dict, Union
from uuid import uuid4

# from db import AccessToken

try:
    import jwt
    from jwt import DecodeError, ExpiredSignatureError
    from tornado.options import options
except ModuleNotFoundError:
    # DB10 fix
    import sys
    sys.path.insert(0, '/afs/cs.pitt.edu/projects/admt/web/sites/db10/beacons/python/site-packages/')

    import jwt
    from jwt import DecodeError, ExpiredSignatureError
    from tornado.options import options

def create_jwt(owner: int,
               id: str=None,
               issuer: str='ADMT Lab',
               issued: datetime=None,
               expires: datetime=None) -> bytes:
    """Creates new JWT for user
    Note: If a JWT currently exists for the user, it is deleted"""
    assert owner is not None
    assert id is None or len(id) == 32
    assert issuer is not None
    assert issued is None or issued <= datetime.utcnow()
    assert expires is None or expires >= datetime.utcnow()

    # set values to defaults
    id = id or uuid4().hex
    issued = issued or datetime.utcnow()
    expires = expires or datetime.utcnow()+timedelta(weeks=2)

    # get app secret
    config = configparser.ConfigParser()
    config.read(options.config)
    secret = config['SERVER'].get('secret')

    # delete old token
    # token = AccessToken.get_by_user(owner)
    # if token is not None:
        # AccessToken.delete(token.id)

    # encode jwt
    encoded = jwt.encode({'id': id, 'own': owner, 'iss': issuer,
                          'iat': issued, 'exp': expires, 'tok': 'Bearer'},
                         secret, algorithm='HS256')
    # encoded = jwt.encode({'own': owner, 'iss': issuer,
                        #   'iat': issued, 'exp': expires, 'tok': 'Bearer'},
                        #  secret, algorithm='HS256')
    # AccessToken.add(id, owner, expires)
    return encoded

def decode_jwt(token: str, verify_exp: bool=False) -> Dict[str, Union[int, str, datetime]]:
    """Decode jwt
    :token: stringified jwt
    :verify_exp: whether to verify jwt expiration
    :returns: decoded token
    :raises DecodeError: if token fails to be decoded
    """
    assert token is not None, 'Token required'

    # get app secret
    config = configparser.ConfigParser()
    config.read(options.config)
    secret = config['SERVER'].get('secret')

    # verify jwt
    decoded = jwt.decode(token, secret, algorithms=['HS256'], options={'verify_exp': verify_exp})
    return decoded


def verify_jwt(token: str) -> bool:
    """Verify token is not expired
    :token: stringified jwt
    :returns: True if not expired
              False if expired
    :raises DecodeError: if token fails to be decoded
    """
    try:
        if decode_jwt(token, True) is not None:
            return True
    except ExpiredSignatureError:
        return False
    except DecodeError:
        raise
