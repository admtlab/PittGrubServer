import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import jwt
from jwt import DecodeError, ExpiredSignatureError

from db import (
    User,
    UserHostRequest,
    UserReferral,
    UserVerification,
    PrimaryAffiliation,
    Property,
    session_scope,
)
from domain.data import UserData, PrimaryAffiliationData
from emailer import send_verification_email
from service.property import get_property, set_property


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


def login(email: str, password: str) -> 'UserData':
    with session_scope() as session:
        if User.verify_credentials(session, email, password):
            user = User.get_by_email(session, email)
            if not user.active:
                verification = UserVerification.get_by_user(session, user.id)
                threshold = int(get_property('user.threshold'))
                if not verification and threshold > 0:
                    verification = UserVerification.add(session, user_id=user.id)
                    send_verification_email(to=email, code=verification.code)
                    set_property('user.threshold', threshold-1)
            user.login_count += 1
            return UserData(user)
    return None


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
            code = None
            threshold = int(get_property('user.threshold'))
            if threshold > 0:
                logging.info("passed threshold")
                code = UserVerification.add(session, user.id).code
                set_property('user.threshold', str(threshold-1))
            else:
                logging.info("failed threshold")
            return UserData(user), code
    return None, None

def get_possible_affiliations():
    with session_scope() as session:
        return [PrimaryAffiliationData(aff) for aff in PrimaryAffiliation.get_all(session)]
    return None

def host_signup(email: str, password: str, name: str, primary_affiliation: int, directory: str, reason: str=None) -> Tuple[Optional['UserData'], Optional[str], bool]:
    with session_scope() as session:
        if PrimaryAffiliation.get_by_id(session,primary_affiliation) is not None:
            user = User.create(session, User(email=email, password=password, name=name, primary_affiliation=primary_affiliation))
            if user is not None:
                code = None
                threshold = int(get_property('user.threshold'))
                if threshold > 0:
                    code = UserVerification.add(session, user.id).code
                    set_property('user.threshold', str(threshold-1))
                host_request = UserHostRequest(user=user.id, primary_affiliation = primary_affiliation, directory=directory, reason=reason)
                session.add(host_request)
                return UserData(user), code, True
            return None, None, True
    return None, None, False

# def get_access_token(id: int) -> 'AccessToken':
#     with session_scope() as session:
#         token = AccessToken.get_by_id(session, id)
#         session.expunge(token)
#         return token

def accept_user_referral(user_email: str, reference_email: str) -> bool:
    with session_scope() as session:
        requester = User.get_by_email(session, user_email)
        reference = User.get_by_email(session, reference_email)
        if requester is None or reference is None:
            return False
        UserReferral()
