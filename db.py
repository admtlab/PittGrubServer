import json, sys
from typing import Any, Optional, List, TypeVar
from sqlalchemy import Column, ForeignKey, BIGINT, CHAR, INT, VARCHAR
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

DEFAULTS = dict({
    'FoodPreference': [
        (1, 'Gluten Free', "No gluten, which is found in wheat, barley, rye, and oat."),
        (2, 'Dairy Free', "No dairy, which includes any items made with cow's milk. This includes milk, butter, cheese, and cream."),
        (3, 'Vegetarian', "No meat, which includes red meat, poultry, and seafood."),
        (4, 'Vegan', "No animal products, including, but not limited to, dairy (milk products), eggs, meat (red meat, poultry, and seafood), and honey."),
    ],
    'User': [
        (1, 'xyz@pitt.edu', '1234567890'),
        (2, 'abc@pitt.edu', '5432109876')
    ],
    'UserFoodPreferences': [
        (1, 1),
        (1, 3),
        (2, 4),
    ],
})

# typing
E = TypeVar('Entity', bound='Entity')


def init(engine, create=False):
    """Initialize database"""
    global session
    session = scoped_session(sessionmaker(bind=engine))
    if create:
        Base.metadata.create_all(bind=engine)
        # add default rows
        for entity, values in DEFAULTS.items():
            cls = getattr(sys.modules[__name__], entity)
            for i in values:
                session.merge(cls(*i))
        session.commit()


class Entity():
    """Base queries for entities"""

    @classmethod
    def get_all(cls) -> List[E]:
        return session.query(cls).all()

    @classmethod
    def get_by_id(cls, id: int) -> Optional[E]:
        return session.query(cls).get(id)


class User(Base, Entity):
    __tablename__ = 'User'

    id = Column('id', BIGINT, primary_key=True, autoincrement=True)
    email = Column('email', VARCHAR(255), unique=True, nullable=False)
    _password = Column('password', CHAR(64), nullable=False)

    def __init__(self, id=None, email=None, password=None):
        self.id = id
        self.email = email
        self._password = password


class FoodPreference(Base, Entity):
    __tablename__ = 'FoodPreference'

    id = Column('id', BIGINT, primary_key=True, autoincrement=True)
    name = Column('name', VARCHAR(255), unique=True, nullable=False)
    description = Column('description', VARCHAR(255), nullable=False)

    def __init__(self, id=None, name=None, description=None):
        self.id = id
        self.name = name
        self.description = description

class UserFoodPreferences(Base):
    __tablename__ = 'UserFoodPreferences'

    user_id = Column("user_id", BIGINT, ForeignKey("User.id"), primary_key=True)
    foodpref_id = Column("foodpreference_id", BIGINT, ForeignKey("FoodPreference.id"), primary_key=True)

    user = relationship("User", foreign_keys=[user_id])
    foodpref = relationship("FoodPreference", foreign_keys=[foodpref_id])

    def __init__(self, user_id, foodpref_id):
        self.user_id = user_id
        self.foodpref_id = foodpref_id

    @classmethod
    def get_all(cls) -> List['UserFoodPreferences']:
        return session.query(cls).all()

    @classmethod
    def get_by_user_id(cls, user_id: int) -> List['UserFoodPreferences']:
        assert user_id is not None
        return session.query(cls).filter_by(user_id=user_id)

    @classmethod
    def get_by_foodpref_id(cls, foodpref_id: int) -> List['UserFoodPreferences']:
        assert foodpref_id is not None
        return session.query(cls).filter_by(foodpreference_i=foodpref_id)


class Event(Base, Entity):
    __tablename__ = 'Event'

    id = Column('id', BIGINT, primary_key=True, autoincrement=True)
    owner_id = Column("owner_id", BIGINT, ForeignKey("User.id"), nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])


class Test(Base, Entity):
    __tablename__ = 'Test'

    id = Column('id', INT, primary_key=True)
    _password = Column('password', CHAR(64), nullable=True)
    private = Column('private', VARCHAR(255), nullable=True)


    def to_json(self):
        return(json.dumps({u'id': self.id}))

    def dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
