import datetime
import random
import string
from typing import Any, Dict, List, Optional, Union

from passlib.hash import bcrypt_sha256
from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship, validates
from sqlalchemy.types import (
    BIGINT, BOOLEAN, CHAR, DateTime, Enum, INT, VARCHAR
)

import db
from db.base import Entity, Password, ReferralStatus, UserStatus

# database db.session variables
Base = declarative_base()


class User(Base, Entity):
    __tablename__ = 'User'

    id = Column('id', BIGINT, primary_key=True, autoincrement=True)
    created = Column('created', DateTime, nullable=False, default=datetime.datetime.utcnow)
    email = Column('email', VARCHAR(255), unique=True, nullable=False)
    password = Column('password', Password, nullable=False)
    status = Column('status', Enum(UserStatus), nullable=False, default=UserStatus.REQUESTED)
    active = Column('active', BOOLEAN, nullable=False, default=False)
    disabled = Column('disabled', BOOLEAN, nullable=False, default=False)
    admin = Column('admin', BOOLEAN, nullable=False, default=False)
    expo_token = Column('expo_token', VARCHAR(255), nullable=True)
    login_count = Column('login_count', INT, nullable=False)

    # mappings
    food_preferences = association_proxy('_user_foodpreferences', 'food_preference')
    recommended_events = association_proxy('_user_recommended_events', 'event')
    accepted_events = association_proxy('_user_accepted_events', 'event')
    checkedin_events = association_proxy('_user_checkedin_events', 'event')

    def __init__(self, id: int=None, email: str=None, password: str=None,
                 status: UserStatus=None, active: bool=False, disabled: bool=False,
                 admin: bool=False, login_count: int=0, expo_token: str=None):
        self.id = id
        self.created = datetime.datetime.utcnow()
        self.email = email
        self.password = password
        self.status = status
        self.active = active
        self.disabled = disabled
        self.admin = admin
        self.login_count = login_count
        self.expo_token = expo_token

    @property
    def valid(self):
        return self.active and self.status is UserStatus.ACCEPTED and not self.disabled

    @classmethod
    def add(cls, email: str, password: str) -> Optional['User']:
        """Create new user and add to database
        :email: user email address
        :password: user password (will be hashed)
        :returns: User, or None duplicate email
        """
        if User.get_by_email(email) is not None:
            return None
        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user

    @classmethod
    def get_by_email(cls, email: str) -> Optional['User']:
        return db.session.query(cls).filter_by(email=email).one_or_none()

    @classmethod
    def verify_credentials(cls, email: str, password: str) -> bool:
        user = User.get_by_email(email)
        if user is None:
            return False
        return bcrypt_sha256.verify(password, user.password)

    @classmethod
    def activate(cls, activation_id: str) -> bool:
        activation = UserVerification.get_by_code(activation_id)
        if activation:
            user = cls.get_by_id(activation.user_id)
            user.active = True
            UserVerification.delete(activation_id)
            db.session.commit()
            return True
        return False

    @classmethod
    def increment_login(cls, id: int):
        assert int is not None
        user = User.get_by_id(id)
        user.login_count += 1
        db.session.commit()

    @classmethod
    def update_preferences(cls, id: int, preferences: List):
        assert id is not None
        assert preferences is not None
        UserFoodPreference.update(id, preferences)

    @classmethod
    def change_password(cls, id: int, new_password: str):
        assert not not new_password
        user = User.get_by_id(id)
        user.password = new_password
        db.session.commit()

    def verify_password(self, password: str) -> bool:
        return bcrypt_sha256.verify(self.password, password)

    def verification(self, verification_code: str) -> bool:
        verification = UserVerification.get_by_user(self.id)
        if verification and verification.code is verification_code:
            self.active = True
            UserVerification.delete(verification_code)

    def add_expo_token(self, expo_token: str):
        self.expo_token = expo_token
        db.session.commit()
        db.session.refresh(self)

    def make_admin(self):
        self.admin = True
        db.session.commit()
        db.session.refresh(self)

    def json(cls, deep: bool=True) -> Dict[str, Any]:
        json = dict(
            id=cls.id,
            email=cls.email,
            active=cls.active,
            admin=cls.admin
        )
        if deep:
            json['food_preferences'] = [f.json() for f in cls.food_preferences]
        else:
            json['food_preferences'] = [f.id for f in cls.food_preferences]
        return json

class UserReferral(Base):
    __tablename__ = 'UserReferral'

    requester = Column('requester', BIGINT, ForeignKey('User.id'), primary_key=True)
    reference = Column('reference', BIGINT, ForeignKey('User.id'))
    status = Column('status', Enum(ReferralStatus), nullable=False, default=ReferralStatus.PENDING)
    time = Column('time', DateTime, default=datetime.datetime.utcnow, nullable=False)

    def __init__(self, requester: int=None, reference: int=None, status: ReferralStatus=None, time: datetime=None):
        self.requester = requester
        self.reference = reference
        self.status = status
        self.time = time

    @classmethod
    def add(cls, requester: int, reference: int) -> 'UserReferral':
        user_referral = UserReferral(requester, reference)
        db.session.add(user_referral)
        db.session.commit()
        db.session.refresh(user_referral)
        return user_referral

    @classmethod
    def get_referral(cls, requester_id: int) -> Optional['UserReferral']:
        assert requester_id > 0
        referral = db.session.query(cls).filter_by(requester=requester_id).one_or_none()
        return referral

    @classmethod
    def get_referrals(cls, reference_id: int) -> List['UserReferral']:
        assert reference_id > 0
        referrals = db.session.query(cls).filter_by(reference=reference_id).all()
        return referrals

    @classmethod
    def get_approved(cls, reference_id: int) -> List['UserReferral']:
        assert reference_id > 0
        referrals = db.session.query(cls).filter_by(reference=reference_id).filter_by(status=ReferralStatus.APPROVED).all()
        return referrals

    @classmethod
    def get_pending(cls, reference_id: int) -> List['UserReferral']:
        assert reference_id > 0
        referrals = db.session.query(cls).filter_by(reference=reference_id).filter_by(status=ReferralStatus.PENDING).all()
        return referrals

    def approve(self):
        user = User.get_by_id(self.requester)
        user.status = UserStatus.APPROVED
        self.status = ReferralStatus.APPROVED
        db.session.commit()
        db.session.refresh(self)

    def deny(self):
        self.status = ReferralStatus.DENIED
        db.session.commit()
        db.session.refresh(self)

    def json(cls, deep: bool=False) -> Dict[str, Any]:
        return dict(
            requester=User.get_by_id(cls.requester).json(),
            reference=cls.reference,
            status=cls.status.value,
            timestamp=cls.time.isoformat()
        )

class FoodPreference(Base, Entity):
    __tablename__ = 'FoodPreference'

    id = Column('id', BIGINT, primary_key=True, autoincrement=True)
    name = Column('name', VARCHAR(255), unique=True, nullable=False)
    description = Column('description', VARCHAR(255), nullable=False)

    def __init__(self, id: int=None, name: str=None, description: str=None):
        self.id = id
        self.name = name
        self.description = description

    def json(cls, deep: bool=False) -> Dict[str, Any]:
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
    def add(cls, user_id: int, foodpreference: Union[int, List[int]]) -> Union['UserFoodPreference', List['UserFoodPreference']]:
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

    @classmethod
    def update(cls, user_id: int, foodpreferences: Union[int, List[int]]):
        cls.delete(user_id)
        cls.add(user_id, foodpreferences)

    @classmethod
    def delete(cls, user_id: int):
        prefs = db.session.query(cls).filter_by(user_id=user_id)
        prefs.delete()
        db.session.commit()

    def json(cls, deep: bool=False) -> Dict[str, Any]:
        if deep:
            return {'user': cls.user.json(False),
                    'food_preference': cls.food_preference.json(deep)}
        else:
            return {'user': cls.user_id,
                    'food_preferences': cls.foodpref_id}


class UserVerification(Base):
    __tablename__ = 'UserVerification'

    code = Column('code', CHAR(6), primary_key=True)
    user_id = Column('user_id', BIGINT, ForeignKey('User.id'), unique=True, nullable=False)

    def __init__(self, code: str, user_id: int):
        self.code = code
        self.user_id = user_id

    @classmethod
    def add(cls, user_id: int, code: str=None) -> 'UserVerification':
        assert user_id is not None
        code = code or cls.generate_code()
        verification = UserVerification(code, user_id)
        db.session.add(verification)
        db.session.commit()
        db.session.refresh(verification)
        return verification

    @classmethod
    def get_by_code(cls, code: str) -> Optional['UserVerification']:
        """Get entity by code"""
        return db.session.query(cls).filter_by(code=code).one_or_none()

    @classmethod
    def get_by_user(cls, user_id: int) -> Optional['UserVerification']:
        """Get entity by user"""
        return db.session.query(cls).filter_by(user_id=user_id).one_or_none()

    @classmethod
    def delete_by_code(cls, code: str) -> bool:
        """Delete instance"""
        success = db.session.query(cls).filter_by(code=code).delete()
        db.session.flush()
        return success

    @classmethod
    def delete(cls, user_id: int) -> bool:
        """Delete instance"""
        success = db.session.query(cls).filter_by(user_id=user_id).delete()
        db.session.flush()
        return success

    @classmethod
    def generate_code(cls) -> str:
        """Generate a new verification code"""
        return ''.join(random.choices(string.ascii_uppercase+string.digits, k=6))


class Event(Base, Entity):
    __tablename__ = 'Event'

    id = Column('id', BIGINT, primary_key=True, autoincrement=True)
    created = Column('created', DateTime, nullable=False, default=datetime.datetime.utcnow)
    organizer_id = Column("organizer", BIGINT, ForeignKey("User.id"), nullable=True)
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

    #@validates('start_date')
    #def validate_start_date(self, key: datetime, start_date: datetime) -> datetime:
    #    assert start_date >= datetime.datetime.now(), "Start date must be after current time"
    #    return start_date

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
    def get_by_id(cls, event_id: int, user_id: int) -> Optional['UserRecommendedEvent']:
        return db.session.query(cls).get([event_id, user_id])

    @classmethod
    def add(cls, user_id: int, event_id: int) -> 'UserRecommendedEvent':
        user_recommended_event = UserRecommendedEvent(event_id, user_id)
        db.session.add(user_recommended_event)
        db.session.commit()
        db.session.refresh(user_recommended_event)
        return user_recommended_event


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
    def get_by_id(cls, event_id: int, user_id: int) -> Optional['UserAcceptedEvent']:
        return db.session.query(cls).get([event_id, user_id])

    @classmethod
    def add(cls, event_id: int, user_id: int) -> 'UserAcceptedEvent':

        user_accepted_event = UserAcceptedEvent.get_by_id(event_id, user_id)
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
    def get_by_id(cls, event_id: int, user_id: int) -> Optional['UserCheckedInEvent']:
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


class AccessToken(Base, Entity):
    __tablename__ = 'AccessToken'

    id = Column('id', CHAR(32), primary_key=True)
    user_id = Column('user_id', BIGINT, ForeignKey('User.id'), unique=True)
    expires = Column('expires', DateTime, nullable=False)

    def __init__(self, id: str, user_id: str, expires: datetime):
        self.id = id
        self.user_id = user_id
        self.expires = expires

    @property
    def valid(self) -> bool:
        return self.expires > datetime.datetime.utcnow()

    # @validates('expires')
    # def validate_expires(self, key: str, expires: datetime) -> str:
    #     """Expiration date should be after current time"""
    #     assert expires > datetime.datetime.now()
    #     return expires

    @classmethod
    def add(cls, id: str, user_id: int, expires: datetime) -> Optional['AccessToken']:
        # validate
        assert expires > datetime.datetime.now()
        assert User.get_by_id(user_id) is not None

        access_token = AccessToken(id, user_id, expires)
        db.session.add(access_token)
        db.session.commit()
        db.session.refresh(access_token)
        return access_token

    @classmethod
    def get_by_user(cls, user_id: int) -> Optional['AccessToken']:
        return db.session.query(cls).filter_by(user_id=user_id).one_or_none()

    @classmethod
    def is_valid(cls, id: str) -> bool:
        token = db.session.query(cls).get(id)
        return token.valid

    @classmethod
    def invalidate(cls, id: str):
        token = db.session.query(cls).get(id)
        token.expire()
        db.session.commit()

    # @classmethod
    # def refresh(cls, id: str, expires: datetime) -> 'AccessToken':
    #     token = db.session.query(cls).get(id)
    #     token.expires = expires
    #     db.session.commit()
    #     db.session.refresh(token)
    #     return token

    @classmethod
    def delete(cls, id: str) -> bool:
        success = db.session.query(cls).filter_by(id=id).delete()
        db.session.commit()
        return success

    def expire(self):
        self.expires = datetime.datetime.now()

    def json(cls) -> Dict[str, Any]:
        return dict(
            token=cls.id,
            user=cls.user_id,
            expires=cls.expires
        )


class EventImage(Base, Entity):
    __tablename__ = "EventImage"

    id = Column('id', BIGINT, primary_key=True, autoincrement=True)
    event_id = Column('event', BIGINT, ForeignKey('Event.id'), unique=False)

    def __init__(self, id: int=None, event_id: int=None):
        self.id = id
        self.event_id = event_id

    @classmethod
    def add(cls, event_id: id) -> 'EventImage':
        event_image = EventImage(event_id=event_id)
        db.session.add(event_image)
        db.session.commit()
        db.session.refresh(event_image)
        return event_image

    @classmethod
    def get_by_event(cls, event_id: int) -> Optional['EventImage']:
        return db.session.query(cls).filter_by(event_id=event_id).one_or_none()
