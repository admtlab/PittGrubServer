import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional, List, TypeVar
from passlib.hash import argon2
from sqlalchemy import create_engine
from sqlalchemy import Column, Table, ForeignKey, ForeignKeyConstraint, String, type_coerce
from sqlalchemy.types import TypeDecorator, DateTime
from sqlalchemy.types import BIGINT, BOOLEAN, CHAR, INT, VARCHAR
from sqlalchemy.orm import deferred, scoped_session, sessionmaker, relationship, backref, validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property, Comparator

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
    # 'UserFoodPreferences': [
    #     (1, 1),
    #     (1, 3),
    #     (2, 4),
    # ],
    # 'Event': [
    #     (1, 1, 'Test Org', 'Free Food Event!', datetime.now(), datetime.now(),
    #      'Test details', 20, 'Sennott Sq', 'Room 6412'),
    # ],
    # 'EventFoodPreferences': [
    #     (1, 1)
    # ],
})

# typing
E = TypeVar('Entity', bound='Entity')


def init(username: str, password: str, url: str, database: str,
         params: str, echo: bool=False, generate: bool=False):
    """Initialize database

    username: username
    password: user's password
    url:      database url
    database: database name
    params:   parameters
    echo:     log commands
    generate: generate tables dynamically
    """

    global session
    engine = create_engine(f"mysql+pymysql://{username}:{password}"
                           f"@{url}/{database}{params}",
                           convert_unicode=True, echo=echo)
    session = scoped_session(sessionmaker(bind=engine))
    if generate:
        Base.metadata.create_all(bind=engine)
        # add default rows
        for entity, values in DEFAULTS.items():
            # get class of entity
            cls = getattr(sys.modules[__name__], entity)
            # merge values
            # this avoids duplicate errors
            for i in values:
                print(*i)
                session.merge(cls(*i))
            session.commit()
        # user = User.get_by_id(1)
        # print(f'user password: {user.password}')
        # print(f'correct password: {DEFAULTS["User"][0][2]}')
        # print(f'hashed: {argon2.hash(DEFAULTS["User"][0][2])}')
        # print(f'hashed: {argon2.hash(DEFAULTS["User"][0][2])}')
        # print(f'verified: {argon2.verify(DEFAULTS["User"][0][2], user.password)}')
        # print(f'default type: {type(DEFAULTS["User"][0][2])}')
        # print(f'user password type: {type(user.password)}')
        # print(f'equality: {DEFAULTS["User"][0][2] == user.password}')


class Entity:
    """Base queries for entities"""

    @classmethod
    def get_all(cls) -> List[E]:
        return session.query(cls).all()

    @classmethod
    def get_by_id(cls, id: int) -> Optional[E]:
        return session.query(cls).get(id)

    def json(cls) -> Dict[str, Any]:
        pass


class Password(TypeDecorator):
    """Argon2 password hash"""
    impl = CHAR(74)

    def process_bind_param(self, value: str, dialect) -> str:
        print(f'bind value: {value}')
        return argon2.hash(value)

    def process_result_value(self, value: str, dialect) -> str:
        print(f'result value: {value}')
        return value

    class comparator_factory(String.comparator_factory):
        def __eq__(self, other: str) -> bool:
            if other is None:
                return False
            else:
                return argon2.verify(other, self.expr)


class User(Base, Entity):
    __tablename__ = 'User'

    id = Column('id', BIGINT, primary_key=True, autoincrement=True)
    email = Column('email', VARCHAR(255), unique=True, nullable=False)
    password = deferred(Column('password', Password, nullable=False))
    active = Column('active', BOOLEAN, nullable=False, default=False)
    disabled = Column('disabled', BOOLEAN, nullable=False, default=False)
    foodpreferences = association_proxy('_user_foodpreferences', 'foodpreference')

    def __init__(self, id: int=None, email: str=None, password: str=None, active: bool=None, disabled: bool=None):
        self.id = id
        self.email = email
        self.password = password
        self.active = active
        self.disabled = disabled

    # @property
    # def password(self):
    #     raise NotImplementedError
    #
    # @password.setter
    # def password(self, password: str):
    #     self._password = Password(password)
    #
    # def verify_password(self, password: str) -> bool:
    #     return argon2.verify(password, self._password)

    @validates('email')
    def validate_email(self, key: str, email: str) -> str:
        assert email.endswith('@pitt.edu')
        return email

    def json(cls, sub=True) -> Dict[str, Any]:
        json = dict({
            'id': cls.id,
            'email': cls.email,
        })
        if sub:
            json['foodpreferences'] = [f.json() for f in cls.foodpreferences]
        return json


class FoodPreference(Base, Entity):
    __tablename__ = 'FoodPreference'

    id = Column('id', BIGINT, primary_key=True, autoincrement=True)
    name = Column('name', VARCHAR(255), unique=True, nullable=False)
    description = Column('description', VARCHAR(255), nullable=False)

    def __init__(self, id: int=None, name: str=None, description: str=None):
        self.id = id
        self.name = name
        self.description = description

    def json(cls) -> Dict[str, Any]:
        return {
            'id': cls.id,
            'name': cls.name,
            'description': cls.description
        }


class UserFoodPreferences(Base):
    __tablename__ = 'UserFoodPreferences'

    user_id = Column('user_id', BIGINT, ForeignKey('User.id'), primary_key=True)
    foodpref_id = Column("foodpreference_id", BIGINT, ForeignKey('FoodPreference.id'), primary_key=True)

    user = relationship(User, backref=backref('_user_foodpreferences'))
    foodpreference = relationship(FoodPreference)

    def __init__(self, user: 'User'=None, foodpreference: 'FoodPreference'=None):
        self.user = user
        self.foodpreference = foodpreference

    def json(cls) -> Dict[str, Any]:
        return {
            'user': cls.user_id,
            'foodpreference': cls.foodpref_id
        }


class Event(Base, Entity):
    __tablename__ = 'Event'

    id = Column('id', BIGINT, primary_key=True, autoincrement=True)
    organizer_id = Column("owner_id", BIGINT, ForeignKey("User.id"), nullable=True)
    organization = Column("organization", VARCHAR(255), nullable=True)
    title = Column('title', VARCHAR(255), nullable=False)
    start_date = Column("start_date", DateTime, nullable=False)
    end_date = Column("end_date", DateTime, nullable=False)
    details = Column("details", VARCHAR(500), nullable=True)
    servings = Column("servings", INT, nullable=False)
    address = Column("address", VARCHAR(255), nullable=False)
    location = Column("location", VARCHAR(255), nullable=False)
    foodpreferences = association_proxy('_event_foodpreferences', 'foodpreference')

    organizer = relationship("User", foreign_keys=[organizer_id])

    def __init__(self,
                 id: int=None,
                 organizer: 'User'=None,
                 organization: str=None,
                 title: str=None,
                 start_date: datetime=None,
                 end_date: datetime=None,
                 details: str=None,
                 servings: int=None,
                 address: str=None,
                 location: str=None):
        self.id = id
        self.organizer = organizer
        self.organization = organization
        self.title = title
        self.start_date = start_date
        self.end_date = end_date
        self.details = details
        self.servings = servings
        self.address = address
        self.location = location

    @classmethod
    def add(cls, title, start_date, end_date, details, servings, address, location) -> 'Event':
        event = Event(title=title, start_date=start_date, end_date=end_date, details=details, servings=servings, address=address, location=location)
        session.add(event)
        session.commit()
        session.refresh(event)
        return event

    def json(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            # 'organizer': self.organizer.json(False),
            # 'organization': self.organization,
            'title': self.title,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'details': self.details,
            'servings': self.servings,
            'address': self.address,
            'location': self.location,
            'foodPreferences': [
                f.json() for f in self.foodpreferences
            ]
        }


class EventFoodPreferences(Base):
    __tablename__ = 'EventFoodPreferences'

    event_id = Column('event_id', BIGINT, ForeignKey('Event.id'), primary_key=True)
    foodpref_id = Column('foodpreference_id', BIGINT, ForeignKey('FoodPreference.id'), primary_key=True)

    event = relationship(Event, backref=backref('_event_foodpreferences'))
    foodpreference = relationship(FoodPreference)

    def __init__(self, event: 'Event'=None, foodpreference: 'FoodPreference'=None):
        self.event = event
        self.foodpreference = foodpreference

    def json(cls) -> Dict[str, Any]:
        return {
            'event': cls.event_id,
            'foodpreference': cls.foodpref_id
        }


class EventType(Base, Entity):
    __tablename__ = 'EventType'

    id = Column('id', BIGINT, primary_key=True, autoincrement=True)
    name = Column('name', VARCHAR(255), unique=True, nullable=False)
    description = Column('description', VARCHAR(255), nullable=False)

    def __init__(self, id: int=None, name: str=None, description: str=None):
        self.id = id
        self.name = name
        self.description = description

    def json(cls) -> Dict[str, Any]:
        return {
            'id': cls.id,
            'name': cls.name,
            'description': cls.description
        }


class EventTypeRel(Base):
    __tablename__ = 'EventTypeRel'

    event_id = Column('event_id', BIGINT, ForeignKey('Event.id'), primary_key=True)
    event_type_id = Column("event_type_id", BIGINT, ForeignKey('EventType.id'), primary_key=True)

    event = relationship(Event, backref=backref('_event_type'))
    event_type = relationship(EventType)

    def __init__(self, event: 'Event'=None, event_type: 'EventType'=None):
        self.event = event
        self.event_type = event_type

    def json(cls) -> Dict[str, Any]:
        return {
            'event': cls.event_id,
            'type': cls.event_type_id
        }


class Test(Base, Entity):
    __tablename__ = 'Test'

    id = Column('id', INT, primary_key=True)
    _password = Column('password', CHAR(64), nullable=True)
    private = Column('private', VARCHAR(255), nullable=True)


    def to_json(self):
        return(json.dumps({u'id': self.id}))

    def dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
