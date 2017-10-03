import enum
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

import db

from passlib.hash import bcrypt_sha256
from sqlalchemy import String, TypeDecorator
from sqlalchemy.types import CHAR

# typing
E = TypeVar('Entity', bound='Entity')


def health_check() -> bool:
    try:
        db.session.execute('SELECT 1')
    except Exception as e:
        log.error(f'Database connection lost\n{e}')
        return False
    return True


class Entity:
    """Base queries for entities"""

    @classmethod
    def get_all(cls) -> List[E]:
        return db.session.query(cls).all()

    @classmethod
    def get_by_id(cls, id: Union[int, str]) -> Optional[E]:
        return db.session.query(cls).get(id)

    @classmethod
    def delete(cls, id: Union[int, str]) -> bool:
        success = db.session.query(cls).filter_by(id=id).delete()
        db.session.commit()
        return success

    def json(cls, deep: bool=False) -> Dict[str, Any]:
        pass


class Password(TypeDecorator):
    """Password hash"""
    impl = CHAR(75)

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
    REFERRAL = 0    # waiting for referral
    REQUESTED = 1   # waiting for verification
    VERIFIED = 2    # verified email account, waiting for activation
    ACCEPTED = 3    # user accepted; active account


class ReferralStatus(enum.Enum):
    PENDING = 'pending'     # waiting for approval
    APPROVED = 'approved'   # referral request approved
    DENIED = 'denied'       # referral request denied
