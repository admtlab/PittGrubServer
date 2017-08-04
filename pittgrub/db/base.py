import db
from typing import (
    Any, Dict, List, Optional, Tuple, TypeVar
)
try:
    from passlib.hash import bcrypt
    from sqlalchemy import String, TypeDecorator
    from sqlalchemy.types import CHAR
except ModuleNotFoundError:
    # DB 10 fix
    import sys
    sys.path.insert(0, '/afs/cs.pitt.edu/projects/admt/web/sites/db10/beacons/python/site-packages/')
    from passlib.hash import bcrypt
    from sqlalchemy import String, TypeDecorator
    from sqlalchemy.types import CHAR


# typing
E = TypeVar('Entity', bound='Entity')


class Entity:
    """Base queries for entities"""

    @classmethod
    def get_all(cls, filters: List[Tuple[str, Any]]=None,
                orders: List[str]=None) -> List[E]:
        # query = session.query(cls)
        # if filters:
        #     query = query.filter_by(**)
        # if orders:
        #     query = query.order_by(*orders)
        # print(f'session query: {session.query(cls)}')
        return db.session.query(cls).all()

    @classmethod
    def get_by_id(cls, id: int) -> Optional[E]:
        return db.session.query(cls).get(id)

    def json(cls, deep: bool=False) -> Dict[str, Any]:
        pass


class Password(TypeDecorator):
    """Password hash"""
    impl = CHAR(60)

    def process_bind_param(self, value: str, dialect) -> str:
        return bcrypt.hash(value)

    def process_result_value(self, value: str, dialect) -> str:
        return value

    class comparator_factory(String.comparator_factory):
        def __eq__(self, other: str) -> bool:
            if other is None:
                return False
            else:
                return bcrypt.verify(other, self.expr)
