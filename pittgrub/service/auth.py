import configparser
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple, Union
from uuid import uuid4

import jwt
from jwt import DecodeError, ExpiredSignatureError
from tornado.options import options

from db import (
    AccessToken,
    Role,
    User,
    UserHostRequest,
    UserReferral,
    UserRole,
    UserVerification,
    session_scope,
)
from domain.data import UserData
from emailer import send_verification_email


class JwtTokenService:
    issuer: str = 'PittGrub'

    def __init__(self, secret: str, alg: str='HS256'):
        assert secret
        self.__secret = secret
        self.__alg = alg

    @property
    def secret(self):
        return self.__secret

    @property
    def alg(self):
        return self.__alg

    def create_access_token(self, owner: int, expires: datetime=None) -> bytes:
        assert owner, 'Owner required'
        assert expires is None or expires >= datetime.utcnow(), 'Expiration must be in the future'
        issued = datetime.utcnow()
        expires = expires or datetime.utcnow()+timedelta(hours=2)

        with session_scope() as session:
            user = User.get_by_id(session, owner)
            roles = [role.name for role in user.roles]
            key = self.secret
            token = jwt.encode(
                payload={'own': owner, 'roles': ','.join(roles),
                         'iss': self.issuer, 'iat': issued, 'exp': expires,},
                key=key,
                algorithm=self.alg,
                headers={'tok': 'acc'})
        return token

    def create_refresh_token(self, owner: int) -> bytes:
        assert owner, 'Owner required'
        issued = datetime.utcnow()

        with session_scope() as session:
            user = User.get_by_id(session, owner)
            roles = [role.name for role in user.roles]
            key = self.secret + user.password
            token = jwt.encode(
                payload={'own': owner, 'roles': ','.join(roles),
                         'iss': self.issuer, 'iat': issued,},
                key=key,
                algorithm=self.alg,
                headers={'tok': 'ref'})
        return token

    def create_password_reset_token(self, owner: int, expires: datetime=None):
        assert owner, 'Owner required'
        assert expires is None or expires >= datetime.utcnow(), 'Expiration must be in the future'

        issued = datetime.utcnow()
        expires = expires or datetime.utcnow()+timedelta(hours=24)

        with session_scope() as session:
            user = User.get_by_id(session, owner)
            roles = [role.name for role in user.roles]
            key = user.password
            token = jwt.encode(
                payload={'own': owner, 'roles': ','.join(roles),
                         'iss': self.issuer, 'iat': issued, 'exp': expires,},
                key=key,
                algorithm=self.alg,
                headers={'tok': 'pas'})
        return token

    def decode_access_token(self, token: str, verify_exp: bool=False) -> Dict[str, Any]:
        assert token, 'Token required'
        assert jwt.get_unverified_header(token).get('tok') == 'acc', 'Access token required'
        return jwt.decode(token, key=self.secret, algorithms=[self.alg], options={'verify_exp': verify_exp})

    def decode_refresh_token(self, token: str) -> Dict[str, Any]:
        assert token, 'Token required'
        assert jwt.get_unverified_header(token).get('tok') == 'ref', 'Refresh token required'
        user = jwt.decode(token, verify=False).get('own')
        with session_scope() as session:
            password = User.get_by_id(session, user).password
        key = self.secret + password
        return jwt.decode(token.encode(), key=key, algorithms=[self.alg], options={'verify_exp': False})

    def decode_password_token(self, token: str, verify_exp: bool=False) -> Dict[str, Any]:
        assert token, 'Token required'
        assert jwt.get_unverified_header(token).get('tok') == 'pas', 'Password reset token required'
        user = jwt.decode(token, verify=False).get('own')
        with session_scope() as session:
            password = User.get_by_id(session, user).password
        return jwt.decode(token, key=password, algorithms=[self.alg], options={'verify_exp': verify_exp})

    def validate_token(self, token: str) -> bool:
        """
        Validate that the token is not expired
        :param token: stringified jwt
        :return: True if valid, False if expired or on error
        """
        assert token, 'Token required'
        token_type = jwt.get_unverified_header(token).get('tok')
        try:
            if token_type == 'acc':
                self.decode_access_token(token, True)
            elif token_type == 'ref':
                self.decode_refresh_token(token)
            elif token_type == 'pas':
                self.decode_password_token(token, True)
            else:
                # return False
                # temporarily assume it's an access token (previous token)
                self.decode_access_token(token, True)
            return True
        except (ExpiredSignatureError, DecodeError):
            return False


def create_jwt(owner: int,
               id: str=None,
               issuer: str='ADMT Lab',
               secret: str=None,
               issued: datetime=None,
               expires: datetime=None) -> bytes:
    """Creates new JWT for user
    Note: If a JWT currently exists for the user, it is deleted"""
    assert owner is not None
    assert id is None or len(id) == 32
    assert issuer is not None
    assert issued is None or issued <= datetime.utcnow()
    assert expires is None or expires >= datetime.utcnow()

    with session_scope() as session:
        user = User.get_by_id(session, owner)
        roles = [role.name for role in user.roles]
        # set values to defaults
        id = id or uuid4().hex
        issued = issued or datetime.utcnow()
        expires = expires or datetime.utcnow()+timedelta(weeks=2)

        # get app secret
        config = configparser.ConfigParser()
        config.read(options.config)
        secret = secret or config['SERVER'].get('secret')

        # delete old token
        # token = AccessToken.get_by_user(owner)
        # if token is not None:
            # AccessToken.delete(token.id)

        # encode jwt
        encoded = jwt.encode({
                'id': id,
                'own': owner,
                'roles': ','.join(roles),
                'iss': issuer,
                'iat': issued,
                'exp': expires,
                'tok': 'Bearer'},
            key=secret, algorithm='HS256')
        # encoded = jwt.encode({'own': owner, 'iss': issuer,
                            #   'iat': issued, 'exp': expires, 'tok': 'Bearer'},
                            #  secret, algorithm='HS256')
        # AccessToken.add(id, owner, expires)
        return encoded

def decode_jwt(token: str, secret: str=None, verify_exp: bool=False) -> Dict[str, Union[int, str, datetime]]:
    """Decode jwt
    :token: stringified jwt
    :secret: the token secret
    :verify_exp: whether to verify jwt expiration
    :returns: decoded token
    :raises DecodeError: if token fails to be decoded
    """
    assert token is not None, 'Token required'

    # get app secret
    config = configparser.ConfigParser()
    config.read(options.config)
    secret = secret or config['SERVER'].get('secret')

    # verify jwt
    decoded = jwt.decode(token, secret, algorithms=['HS256'], options={'verify_exp': verify_exp})
    return decoded

def verify_jwt(token: str, secret: str=None) -> bool:
    """Verify token is not expired
    :token: stringified jwt
    :returns: True if not expired
              False if expired
    :raises DecodeError: if token fails to be decoded
    """
    try:
        if decode_jwt(token=token, secret=secret, verify_exp=True) is not None:
            return True
    except ExpiredSignatureError:
        return False
    except DecodeError:
        raise

def login(email: str, password: str) -> 'UserData':
    with session_scope() as session:
        if User.verify_credentials(session, email, password):
            user = User.get_by_email(session, email)
            if not user.active:
                verification = UserVerification.get_by_user(session, user.id)
                if not verification:
                    verification = UserVerification.add(session, user_id=user.id)
                    send_verification_email(to=email, activation=verification.code)
            user.inc_login()
            return UserData(user)
    return None

def logout(access_token_id: int) -> bool:
    with session_scope() as session:
        AccessToken.delete(session, access_token_id)

def signup(email: str, password: str, name: str=None) -> Tuple[Optional['UserData'], Optional[str]]:
    """
    Sign user up with
    :param email:
    :param password:
    :param name:
    :return:
    """
    with session_scope() as session:
        user = User.create(session, User(email=email, password=password))
        if user is not None:
            activation = UserVerification.add(session, user.id)
            return UserData(user), activation.code
    return None, None


def host_signup(email: str, password: str, name: str, organization: str, directory: str, reason: str=None) -> Tuple[Optional['UserData'], Optional[str]]:
    with session_scope() as session:
        user = User.create(session, User(email=email, password=password, name=name))
        if user is not None:
            activation = UserVerification.add(session, user.id)
            host_request = UserHostRequest(user=user.id, organization=organization, directory=directory, reason=reason)
            session.add(host_request)
            return UserData(user), activation.code
    return None, None

def approve_host(user_id: int, admin_id: int) -> bool:
    with session_scope() as session:
        admin = User.get_by_id(session, admin_id)
        session.add(UserRole(user_id, Role.get_by_name(session, 'Host').id))
        assert admin is not None
        assert 'Admin' in [r.name for r in admin.roles]
        return UserHostRequest.approve_host(session, user_id, admin_id)

def get_access_token(id: int) -> 'AccessToken':
    with session_scope() as session:
        token = AccessToken.get_by_id(session, id)
        session.expunge(token)
        return token

def accept_user_referral(user_email: str, reference_email: str) -> bool:
    with session_scope() as session:
        requester = User.get_by_email(session, user_email)
        reference = User.get_by_email(session, reference_email)
        if requester is None or reference is None:
            return False
        UserReferral()
