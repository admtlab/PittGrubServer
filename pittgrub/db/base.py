import enum
import logging
from typing import List, Optional, Type, TypeVar, Union

from passlib.hash import bcrypt_sha256
from sqlalchemy import String, TypeDecorator
from sqlalchemy.types import CHAR

import db


# typing
E = TypeVar('Entity', bound='Entity')


def health_check() -> bool:
    try:
        with db.session_scope() as session:
            session.execute('SELECT 1')
        return True
    except Exception as e:
        logging.info(e)
        return False


class Entity:
    """Base queries for entities"""

    @classmethod
    def get_all(cls: Type[E], session) -> List[Type[E]]:
        entities = session.query(cls).all()
        return entities

    @classmethod
    def get_by_id(cls: Type[E], session, entity_id: Union[int, str]) -> Optional[Type[E]]:
        entity = session.query(cls).get(entity_id)
        return entity

    @classmethod
    def delete(cls: Type[E], session, entity_id: Union[int, str]) -> bool:
        success = session.query(cls)\
            .filter_by(id=entity_id)\
            .delete()
        return success

class Password(TypeDecorator):
    """Password hash
    Hash is SHA-256
    """

    impl = CHAR(75)

    def process_literal_param(self, value: str, dialect):
        return value if value is not None else None

    def process_bind_param(self, value: str, dialect) -> str:
        return bcrypt_sha256.hash(value)

    def process_result_value(self, value: str, dialect) -> str:
        return value

    class comparator_factory(String.comparator_factory):
        def __eq__(self, other: str) -> bool:
            if other is None:
                return False
            else:
                return bcrypt_sha256.verify(other, self.expr)


class UserStatus(enum.Enum):
    REFERRAL = 0  # waiting for referral
    REQUESTED = 1  # waiting for verification
    VERIFIED = 2  # verified email account, waiting for activation
    ACCEPTED = 3  # user accepted; active account


class Activity(enum.Enum):
    LOGIN = 0
    LOGOUT = 1
    ACTIVE = 2
    INACTIVE = 3
    BACKGROUND = 4
    REFRESH = 5

# class UserRole(enum.Enum):
#     USER = 0    # normal user
#     ADMIN = 1   # creates events and accepts non-pitt email addresses
#     SUPER = 2   # makes admins and groups, approves users when limiting is on
#
#
# class UserRoleNew(enum.Enum):
#     USER = 0    # Normal user
#     HOST = 1    # Host (create events)
#     ADMIN = 2   # Make hosts and groups


class OrganizationRole(enum.Enum):
    """
    The role of the user belonging to an organization
    """
    MEMBER = 0  # Normal member
    HOST = 1  # Host (creates events on behalf of organization)


class ReferralStatus(enum.Enum):
    PENDING = 'pending'  # waiting for approval
    APPROVED = 'approved'  # referral request approved
    DENIED = 'denied'  # referral request denied
