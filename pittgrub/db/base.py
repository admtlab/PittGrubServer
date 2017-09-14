import enum
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

from pittgrub import db

try:
    from passlib.hash import bcrypt_sha256
    from sqlalchemy import String, TypeDecorator
    from sqlalchemy.types import CHAR
except ModuleNotFoundError:
    # DB 10 fix
    import sys
    sys.path.insert(0, '/afs/cs.pitt.edu/projects/admt/web/sites/db10/beacons/python/site-packages/')

    from passlib.hash import bcrypt_sha256
    from sqlalchemy import String, TypeDecorator
    from sqlalchemy.types import CHAR


# typing
E = TypeVar('Entity', bound='Entity')


class Entity:
    """Base queries for entities"""

    @classmethod
    def get_all(cls, filters: List[Tuple[str, Any]]=[], orders: List[str]=[]) -> List[E]:
        # query = session.query(cls)
        # if filters:
        #     query = query.filter_by(**)
        # if orders:
        #     query = query.order_by(*orders)
        # print(f'session query: {session.query(cls)}')
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
    WAITING = 0     # waiting for referral
    APPROVED = 1    # referral approved
    REQUESTED = 2   # requested access
    ACCEPTED = 3    # request accepted, sent verification
    VERIFIED = 4    # verified,

class ReferralStatus(enum.Enum):
    REQUESTED = 0   # waiting for approval
    APPROVED = 1    # referral request approved
    DENIED = 2      # referral request denied