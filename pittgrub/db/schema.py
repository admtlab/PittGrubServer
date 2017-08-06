import datetime
import json
from typing import Any, Dict, List, Optional, Union

import db
from db.base import Entity, Password

try:
    from passlib.hash import bcrypt_sha256
    from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, Table
    from sqlalchemy.types import DateTime, TypeDecorator
    from sqlalchemy.types import BIGINT, BOOLEAN, CHAR, INT, VARCHAR
    from sqlalchemy.orm import (
        backref, deferred, relationship,
        scoped_session, sessionmaker, validates
    )
    from sqlalchemy.ext.associationproxy import association_proxy
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.ext.hybrid import Comparator, hybrid_property
except ModuleNotFoundError:
    # DB10 fix
    import sys
    sys.path.insert(0, '/afs/cs.pitt.edu/projects/admt/web/sites/db10/beacons/python/site-packages/')

    from passlib.hash import bcrypt_sha256
    from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint, Table
    from sqlalchemy.types import DateTime, TypeDecorator
    from sqlalchemy.types import BIGINT, BOOLEAN, CHAR, INT, VARCHAR
    from sqlalchemy.orm import (
        backref, deferred, relationship,
        scoped_session, sessionmaker, validates
    )
    from sqlalchemy.ext.associationproxy import association_proxy
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.ext.hybrid import Comparator, hybrid_property


# database db.session variables
Base = declarative_base()


class User(Base, Entity):
    __tablename__ = 'User'

    id = Column('id', BIGINT, primary_key=True, autoincrement=True)
    email = Column('email', VARCHAR(255), unique=True, nullable=False)
    password = deferred(Column('password', Password, nullable=False))
    active = Column('active', BOOLEAN, nullable=False, default=False)
    disabled = Column('disabled', BOOLEAN, nullable=False, default=False)
    expo_token = Column('expo_token', VARCHAR(255), nullable=True)

    # mappings
    food_preferences = association_proxy('_user_foodpreferences', 'food_preference')
    recommended_events = association_proxy('_user_recommended_events', 'event')
    accepted_events = association_proxy('_user_accepted_events', 'event')
    checkedin_events = association_proxy('_user_checkedin_events', 'event')

    def __init__(self, id: int=None, email: str=None, password: str=None,
                 active: bool=None, disabled: bool=None, expo_token: str=None):
        self.id = id
        self.email = email
        self.password = password
        self.active = active
        self.disabled = disabled
        self.expo_token = expo_token

    @validates('email')
    def validate_email(self, key: str, email: str) -> str:
        assert email.endswith('@pitt.edu')
        return email

    @classmethod
    def get_by_email(cls, email: str) -> Optional['User']:
        return db.session.query(cls).filter(User.email == email).one_or_none()

    @classmethod
    def verify(cls, email: str, password: str) -> bool:
        user = User.get_by_email(email)
        if user is None:
            return False
        return bcrypt_sha256.verify(password, user.password)

    @classmethod
    def add_expo_token(cls, id: int, expo_token: str) -> bool:
        try:
            user = User.get_by_id(id)
            user.expo_token = expo_token
            db.session.commit()
            return True
        except:
            return False

    def json(cls, deep: bool=True) -> Dict[str, Any]:
        json = dict({
            'id': cls.id,
            'email': cls.email,
        })
        if deep:
            json['food_preferences'] = [f.json() for f in cls.food_preferences]
        else:
            json['food_preferences'] = [f.id for f in cls.food_preferences]
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


class UserFoodPreference(Base):
    __tablename__ = 'UserFoodPreference'

    user_id = Column('user_id', BIGINT, ForeignKey('User.id'), primary_key=True)
    foodpref_id = Column("foodpreference_id", BIGINT, ForeignKey('FoodPreference.id'), primary_key=True)

    user = relationship(User, backref=backref('_user_foodpreferences'))
    food_preference = relationship(FoodPreference)

    def __init__(self, user: int=None, foodpreference: int=None):
        self.user_id = user
        self.foodpref_id = foodpreference

    @classmethod
    def add(cls, use_id: int, foodpreference: Union[int, List[int]]) -> Union['UserFoodPreference', List['UserFoodPreference']]:

        if isinstance(foodpreference, list):
            user_foodpreferences = []
            for fp in foodpreference:
                user_foodpreference = UserFoodPreference(user_id, fp)
                db.session.add(user_foodpreference)
                user_foodpreferences.append(user_foodpreference)
        else:
            user_foodpreferences = UserFoodPreference(user_id, foodpreference)
            db.session.add(user_foodpreference)
        db.session.commit()
        return user_foodpreferences

    def json(cls, deep: bool=False) -> Dict[str, Any]:
        if deep:
            return {
                'user': cls.user.json(False),
                'food_preference': cls.food_preference.json()
            }
        else:
            return {
                'user': cls.user_id,
                'food_preferences': cls.foodpref_id
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
    servings = Column("servings", INT, nullable=True)
    address = Column("address", VARCHAR(255), nullable=False)
    location = Column("location", VARCHAR(255), nullable=False)

    # mappings
    food_preferences = association_proxy('_event_foodpreferences', 'food_preference')
    recommended_users = association_proxy('_event_recommended_users', 'user')
    accepted_users = association_proxy('_event_accepted_users', 'user')
    checkin_users = association_proxy('_event_checkedin_users', 'user')

    organizer = relationship("User", foreign_keys=[organizer_id])

    def __init__(self, id: int=None, organizer: int=None,
                 organization: str=None, title: str=None,
                 start_date: datetime=None, end_date: datetime=None,
                 details: str=None, servings: int=None,
                 address: str=None, location: str=None):
        self.id = id
        self.organizer_id = organizer
        self.organization = organization
        self.title = title
        self.start_date = start_date
        self.end_date = end_date
        self.details = details
        self.servings = servings
        self.address = address
        self.location = location

    @classmethod
    def add(cls, title: str, start_date: datetime, end_date: datetime,
            details: str, servings: int, address: str, location: str) -> 'Event':
        event = Event(title=title, start_date=start_date, end_date=end_date,
                      details=details, servings=servings, address=address,
                      location=location)
        db.session.add(event)
        db.session.commit()
        db.session.refresh(event)
        return event

    @validates('start_date')
    def validate_start_date(self, key: datetime, start_date: datetime) -> datetime:
        assert start_date >= datetime.datetime.now(), "Start date must be after current time"
        return start_date

    @validates('end_date')
    def validate_end_date(self, key: datetime, end_date: datetime) -> datetime:
        assert end_date > self.start_date, "End date must come after start date"
        return end_date

    def json(self, deep: bool=False) -> Dict[str, Any]:
        data = {
            'id': self.id,
            'organization': self.organization,
            'title': self.title,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'details': self.details,
            'servings': self.servings,
            'address': self.address,
            'location': self.location,
            'food_preferences': [
                f.json() for f in self.food_preferences
            ]
        }

        if self.organizer is not None:
            if deep:
                data['organizer'] = self.organizer.json(False)
            else:
                data['organizer'] = self.organizer.id

        return data


class EventFoodPreference(Base):
    __tablename__ = 'EventFoodPreference'

    event_id = Column('event_id', BIGINT, ForeignKey('Event.id'), primary_key=True)
    foodpref_id = Column('foodpreference_id', BIGINT, ForeignKey('FoodPreference.id'), primary_key=True)

    event = relationship(Event, backref=backref('_event_foodpreferences'))
    food_preference = relationship(FoodPreference)

    def __init__(self, event: int=None, foodpreference: int=None):
        self.event_id = event
        self.foodpref_id = foodpreference

    @classmethod
    def get_by_id(cls, event_id: int, foodpreference_id: int) -> Optional['EventFoodPreference']:
        return db.session.query(cls).get([event_id, foodpreference_id])

    @classmethod
    def add(cls, event_id: int, foodpreference: Union[int, List[int]]) -> Union['EventFoodPreference', List['EventFoodPreference']]:

        if isinstance(foodpreference, list):
            event_foodpreferences = []
            for fp in foodpreference:
                event_foodpreference = EventFoodPreference.get_by_id(event_id, fp)
                if not event_foodpreference:
                    event_foodpreference = EventFoodPreference(event_id, fp)
                    db.session.add(event_foodpreference)
                event_foodpreferences.append(event_foodpreference)
        else:
            event_foodpreferences = EventFoodPreference.get_by_id(event_id, foodpreference)
            if not event_foodpreferences:
                event_foodpreferences = EventFoodPreference(event_id, foodpreference)
                db.session.add(event_foodpreferences)
        db.session.commit()
        return event_foodpreferences

    def json(cls, deep: bool=False) -> Dict[str, Any]:
        if deep:
            return {
                'event': cls.event.json(deep),
                'food_preference': cls.food_preference.json()
            }
        else:
            return {
                'event': cls.event_id,
                'food_preference': cls.foodpref_id
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


class UserRecommendedEvent(Base):
    __tablename__ = 'UserRecommendedEvent'

    event_id = Column('event_id', BIGINT, ForeignKey('Event.id'), primary_key=True)
    user_id = Column('user_id', BIGINT, ForeignKey('User.id'), primary_key=True)
    time = Column('time', DateTime, default=datetime.datetime.utcnow, nullable=False)

    event = relationship(Event, backref=backref('_event_recommended_users'))
    user = relationship(User, backref=backref('_user_recommended_events'))

    def __init__(self, event_id: int, user_id: int, time: datetime=None):
        self.event_id = event_id
        self.user_id = user_id
        self.time = time

    @classmethod
    def find_by_id(cls, event_id: int, user_id: int) -> Optional['UserRecommendedEvent']:
        return db.session.query(cls).get([event_id, user_id])

    def json(cls, deep: bool=False) -> Dict[str, Any]:
        if deep:
            return {
                'event': cls.event.json(deep),
                'user': cls.user.json(False),
                'time': cls.time
            }
        else:
            return {
                'event': cls.event_id,
                'user': cls.user_id,
                'time': cls.time
            }


class UserAcceptedEvent(Base):
    __tablename__ = 'UserAcceptedEvent'

    event_id = Column('event_id', BIGINT, ForeignKey('Event.id'), primary_key=True)
    user_id = Column('user_id', BIGINT, ForeignKey('User.id'), primary_key=True)
    time = Column('time', DateTime, default=datetime.datetime.utcnow, nullable=False)

    event = relationship(Event, backref=backref('_event_accepted_users'))
    user = relationship(User, backref=backref('_user_accepted_events'))

    def __init__(self, event_id: int, user_id: int, time: datetime=None):
        self.event_id = event_id
        self.user_id = user_id
        self.time = time

    @classmethod
    def find_by_id(cls, event_id: int, user_id: int) -> Optional['UserAcceptedEvent']:
        return db.session.query(cls).get([event_id, user_id])

    @classmethod
    def add(cls, event_id: int, user_id: int) -> 'UserAcceptedEvent':

        user_accepted_event = UserAcceptedEvent.find_by_id(event_id, user_id)
        if not user_accepted_event:
            user_accepted_event = UserAcceptedEvent(event_id, user_id)
            db.session.add(user_accepted_event)
            db.session.commit()
        return user_accepted_event

    def json(cls, deep: bool=False) -> Dict[str, Any]:
        if deep:
            return {
                'event': cls.event.json(deep),
                'user': cls.user.json(False),
                'time': cls.time
            }
        else:
            return {
                'event': cls.event_id,
                'user': cls.user_id,
                'time': cls.time
            }


class UserCheckedInEvent(Base):
    __tablename__ = 'UserCheckedInEvent'

    event_id = Column('event_id', BIGINT, ForeignKey('Event.id'), primary_key=True)
    user_id = Column('user_id', BIGINT, ForeignKey('User.id'), primary_key=True)
    time = Column('time', DateTime, default=datetime.datetime.utcnow, nullable=False)

    event = relationship(Event, backref=backref('_event_checkedin_users'))
    user = relationship(User, backref=backref('_user_checkedin_events'))

    def __init__(self, event_id: int, user_id: int, time: datetime=None):
        self.event_id = event_id
        self.user_id = user_id
        self.time = time

    @classmethod
    def find_by_id(cls, event_id: int, user_id: int) -> Optional['UserCheckedInEvent']:
        return db.session.query(cls).get([event_id, user_id])

    def json(cls, deep: bool=False) -> Dict[str, Any]:
        if deep:
            return {
                'event': cls.event.json(deep),
                'user': cls.user.json(False),
                'time': cls.time
            }
        else:
            return {
                'event': cls.event_id,
                'user': cls.user_id,
                'time': cls.time
            }


# class Test(Base, Entity):
#     __tablename__ = 'Test'
#     id = Column('id', INT, primary_key=True)
#     _password = Column('password', CHAR(64), nullable=True)
#     private = Column('private', VARCHAR(255), nullable=True)
#     def to_json(self):
#         return(json.dumps({u'id': self.id}))
#     def dict(self):
#         return {c.name: getattr(self, c.name) for c in self.__table__.columns}
