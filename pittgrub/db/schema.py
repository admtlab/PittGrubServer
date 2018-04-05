import datetime
import logging
import random
import string
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from passlib.hash import bcrypt_sha256
from sqlalchemy import Column, ForeignKey
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relationship, validates
from sqlalchemy.types import (
    BIGINT, BOOLEAN, CHAR, DECIMAL, DateTime, Enum, INT, VARCHAR, SMALLINT
)

import db
from db.base import Entity, Password, OrganizationRole, ReferralStatus, UserStatus

# database db.session variables
Base = declarative_base()


class User(Base, Entity):
    __tablename__ = 'User'

    id = Column('id', BIGINT, primary_key=True, autoincrement=True)
    created = Column('created', DateTime, nullable=False, default=datetime.datetime.utcnow)
    email = Column('email', VARCHAR(255), unique=True, nullable=False)
    password = Column('password', Password, nullable=False)
    status = Column('status', Enum(UserStatus), nullable=False, default=UserStatus.REQUESTED)
    name = Column('name', VARCHAR(255), unique=False, nullable=True)
    active = Column('active', BOOLEAN, nullable=False, default=False)
    disabled = Column('disabled', BOOLEAN, nullable=False, default=False)
    # host = Column('host', BOOLEAN, nullable=False, default=False)
    expo_token = Column('expo_token', VARCHAR(255), nullable=True)
    login_count = Column('login_count', INT, nullable=False)
    pitt_pantry = Column('pitt_pantry', BOOLEAN, nullable=False, default=False)
    eagerness = Column('eagerness', INT, nullable=False, default=3)

    # mappings
    roles = association_proxy('_user_roles', 'role')
    expo_tokens = association_proxy('_user_expo_tokens', 'token')
    food_preferences = association_proxy('_user_foodpreferences', 'food_preference')
    recommended_events = association_proxy('_user_recommended_events', 'event')
    accepted_events = association_proxy('_user_accepted_events', 'event')
    checkedin_events = association_proxy('_user_checkedin_events', 'event')

    def __init__(self, id: int=None, email: str=None, password: str=None,
                 status: UserStatus=None, name: str=None,
                 active: bool=False, disabled: bool=False,
                 login_count: int=0, expo_token: str=None,
                 pitt_pantry: bool=False, eagerness: int=3):
        self.id = id
        self.created = datetime.datetime.utcnow()
        self.email = email
        self.password = password
        self.status = status
        self.name = name
        self.active = active
        self.disabled = disabled
        # self.host = host
        self.login_count = login_count
        self.expo_token = expo_token
        self.pitt_pantry = pitt_pantry
        self.eagerness = eagerness

    @property
    def valid(self):
        """Check if user is valid i.e., active, ACCEPTED, and not disables
        """
        return self.active and self.status is UserStatus.ACCEPTED and not self.disabled

    @property
    def is_admin(self) -> bool:
        return 'Admin' in [r.name for r in self.roles]

    @classmethod
    def get_by_email(cls, session, email: str) -> Optional['User']:
        """
        Get user by email
        :param session: database session
        :param email:   user email
        :return:        user
        """
        return session.query(cls).filter_by(email=email).one_or_none()

    @classmethod
    def get_roles(cls, session, user_id) -> List['Role']:
        """
        Get roles belonging to user
        :param session: database session
        :param user_id: id of user
        :return:        roles
        """
        user_roles = session.query(UserRole).filter_by(user_id=user_id).all()
        return [r.role for r in user_roles]

    @classmethod
    def create(cls, session, user: 'User', roles: List['Role']=None) -> Optional['User']:
        """
        Create new user and add to database
        Will always be given the role User
        :param session: database session
        :param user:    user object
        :param role:    user role (always adds User by default)
        :return:        user, or none if error
        """
        if User.get_by_email(session, user.email) is not None:
            return None
        session.add(user)
        session.commit()
        session.refresh(user)
        session.add(UserRole(user.id, Role.get_by_name(session, 'User').id))
        if roles is not None:
            for role in roles:
                session.add(UserRole(user.id, role.id))
        return user

    @classmethod
    def verify_credentials(cls, session, email: str, password: str) -> bool:
        user = User.get_by_email(session, email)
        if user is None:
            return False
        return bcrypt_sha256.verify(password, user.password)

    @classmethod
    def activate(cls, session, activation_id: str) -> bool:
        activation = UserVerification.get_by_code(session, activation_id)
        if activation:
            user = cls.get_by_id(session, activation.user_id)
            user.active = True
            user.status = UserStatus.ACCEPTED
            UserVerification.delete(session, activation_id)
            return True
        return False

    @classmethod
    def increment_login(cls, session, id: int):
        assert int is not None
        user = User.get_by_id(session, id)
        user.login_count += 1

    @classmethod
    def update_preferences(cls, session, id: int, preferences: List):
        assert id is not None
        assert preferences is not None
        UserFoodPreference.update(session, id, preferences)

    @classmethod
    def change_password(cls, session, id: int, new_password: str):
        assert not not new_password
        user = User.get_by_id(session, id)
        user.password = new_password

    def verify_password(self, password: str) -> bool:
        return bcrypt_sha256.verify(self.password, password)

    def verification(self, session, verification_code: str) -> bool:
        verification = UserVerification.get_by_user(session, self.id)
        if verification and verification.code is verification_code:
            self.active = True
            UserVerification.delete(session, verification_code)

    def add_expo_token(self, expo_token: str):
        self.expo_token = expo_token

    def inc_login(self):
        self.login_count += 1

    # def make_host(self, session):
    #     self.host = True
    #     db.session.commit()
    #     db.session.refresh(self)

    def make_host(self, session):
        host_role = Role.get_by_name(session, 'Host')
        user_role = UserRole(self.id, host_role.id)
        session.add(user_role)

    def update_eagerness(self, value: int):
        assert 0 < value
        self.eagerness = value
        db.session.commit()
        db.session.refresh(self)

    def set_pitt_pantry(self, status: bool):
        assert status is not None
        self.pitt_pantry = status
        db.session.commit()
        db.session.refresh(self)

    def json_info(cls) -> Dict[str, Union[bool, int, str]]:
        """Get json serializable representation of account related info"""
        return dict(
            id=cls.id,
            active=cls.active,
            host=cls.host,
            status=cls.status.name)

    def json_settings(cls) -> Dict[str, Any]:
        """Get json serializable representation of user settings"""
        return dict(
            eagerness=cls.eagerness,
            pantry=cls.pitt_pantry,
            food_preferences=[f.json() for f in cls.food_preferences])

    @classmethod
    def to_json(self, user: 'User') -> Dict[str, Any]:
        with db.session_scope() as session:
            session.add(user)
            json = dict(
                    id=user.id,
                    email=user.email,
                    status=user.status.name,
                    roles=[role.json() for role in user.roles],
                    eagerness=user.eagerness,
                    pantry=user.pitt_pantry,
                    food_preferences=[f.json() for f in user.food_preferences]
            )
        return json

    def json(cls, deep: bool=True) -> Dict[str, Any]:
        json = dict(
            id=cls.id,
            email=cls.email,
            status=cls.status.name,
            eagerness=cls.eagerness,
            pantry=cls.pitt_pantry
        )
        if deep:
            json['food_preferences'] = [f.json() for f in cls.food_preferences]
        else:
            json['food_preferences'] = [f.id for f in cls.food_preferences]
        return json


def create_user(session, user: User, role: 'Role'=None) -> Optional[User]:
        if session.query(User).filter_by(email=user.email).one_or_none() is not None:
            return None
        role = role or session.query(Role).filter_by(name='User').one_or_none()
        session.add(user)
        session.commit()
        session.refresh(user)
        session.add(UserRole(user.id, role.id))
        return user


class Role(Base, Entity):
    """
    Roles for users with privileges
    """
    __tablename__ = 'Role'

    id = Column('id', SMALLINT, primary_key=True, autoincrement=True)
    name = Column('name', VARCHAR(10), unique=True, nullable=False)
    description = Column('description', VARCHAR(500), nullable=False)
    
    def __init__(self, id: int=None, name: str=None, description: str=None):
        self.id = id
        self.name = name
        self.description = description

    @classmethod
    def get_by_name(cls, session, name: str) -> Optional['Role']:
        return session.query(cls).filter_by(name=name).one_or_none()

    def json(self):
        return dict({'id': self.id, 'name': self.name})



class UserRole(Base):
    """
    User role relationship
    """
    __tablename__ = 'UserRole'

    user_id = Column('user_id', BIGINT, ForeignKey('User.id'), primary_key=True)
    role_id = Column('role_id', SMALLINT, ForeignKey('Role.id'), primary_key=True)

    user = relationship(User, backref=backref('_user_roles'))
    role = relationship(Role)

    def __init__(self, user_id: int=None, role_id: int=None):
        self.user_id = user_id
        self.role_id = role_id

    @classmethod
    def add(cls, session, user_id: int, role_name: str) -> 'UserRole':
        user_role = UserRole(user_id, Role.get_by_name(session, role_name).id)
        session.add(user_role)


class Organization(Base, Entity):
    """
    NOT CURRENTLY USED
    """
    __tablename__ = 'Organization'

    id = Column('id', BIGINT, primary_key=True, autoincrement=True)
    name = Column('name', VARCHAR(255), unique=True, nullable=False)
    description = Column('description', VARCHAR(255), nullable=False)
    url = Column('url', VARCHAR(512), unique=False, nullable=True)
    created = Column('created', DateTime, nullable=False, default=datetime.datetime.utcnow)

    def __init__(self, id: int=None, name: str=None, description: str=None, url: str=None):
        self.id = id
        self.name = name
        self.description = description
        self.url = url
        self.created = datetime.datetime.utcnow()


class UserOrganization(Base):
    """
    NOT CURRENLTY USED
    """
    __tablename__ = 'UserOrganization'

    user_id = Column('user_id', BIGINT, ForeignKey('User.id'), primary_key=True)
    organization_id = Column('organization_id', BIGINT, ForeignKey('Organization.id'), primary_key=True)
    role = Column('role', Enum(OrganizationRole), nullable=False, default=OrganizationRole.MEMBER)

    user = relationship(User, backref=backref('_user_organizations'))
    organization = relationship(Organization)

    def __init__(self, user: int=None, organization: int=None, role: OrganizationRole=None):
        self.user_id = user
        self.organization_id = organization
        self.role = role

    @classmethod
    def add(cls, user_id: int, organization_id: int, role: OrganizationRole=OrganizationRole.MEMBER) -> 'UserOrganization':
        userOrg = UserOrganization(user_id, organization_id, role)
        db.session.add(userOrg)


class UserHostRequest(Base, Entity):
    __tablename__ = 'UserHostRequest'

    id = Column('id', BIGINT, primary_key=True, autoincrement=True)
    user_id = Column('user', BIGINT, ForeignKey("User.id"), unique=True, nullable=False)
    organization = Column('organization', VARCHAR(255), nullable=False)
    directory = Column('directory', VARCHAR(512), nullable=False)
    reason = Column('reason', VARCHAR(500), nullable=True)
    created = Column('created', DateTime, nullable=False, default=datetime.datetime.utcnow)
    approved = Column('approved', DateTime, nullable=True)
    approved_by = Column('approved_by', BIGINT, ForeignKey("User.id"), unique=False, nullable=True)

    user = relationship('User', foreign_keys=[user_id], backref='user')
    admin_approval = relationship('User', foreign_keys=[approved_by])

    def __init__(self, id: int=None, user: int=None, organization: str=None, directory: str=None, reason: str=None):
        self.id = id
        self.user_id = user
        self.organization = organization
        self.directory = directory
        self.reason = reason
        self.created = datetime.datetime.utcnow()
        self.approved = None
        self.approved_by = None

    @classmethod
    def get_by_user_id(cls, session, user_id: int) -> Optional['UserHostRequest']:
        return session.query(cls).filter_by(user_id=user_id).one_or_none()

    @classmethod
    def get_all_pending(cls, session):
        return session.query(cls).filter(cls.approved.is_(None)).all()

    @classmethod
    def approve_host(cls, session, user_id: int, admin_id: int) -> bool:
        user_host_req = UserHostRequest.get_by_user_id(session, user_id)
        if user_host_req is None or user_host_req.approved is not None:
            return False
        user_host_req.approved = datetime.datetime.utcnow()
        user_host_req.approved_by = admin_id
        session.merge(user_host_req)
        session.commit()
        return True

    @classmethod
    def add(cls, user_id, organization, directory, reason):
        host_request = UserHostRequest(user=user_id, organization=organization, directory=directory, reason=reason)
        db.session.add(host_request)
        db.session.commit()

    def json(self, deep=False):
        with db.session_scope() as session:
            session.add(self)
            return dict({
                'id': self.id,
                'user': dict({ 'id': self.user_id, 'email': self.user.email, 'name': self.user.name }),
                'organization': self.organization,
                'directory': self.directory,
                'reason': self.reason,
                'created': self.created.isoformat()
            })


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


class ExpoToken(Base):
    __tablename__ = 'ExpoToken'

    user_id = Column('user', BIGINT, ForeignKey('User.id'), primary_key=True)
    token = Column('token', VARCHAR(255), unique=True, nullable=False, primary_key=True)

    user = relationship(User, backref=backref('_user_expo_tokens'))

    def __int__(self, user_id: int, token: str):
        self.user_id = user_id
        self.token = token

    @classmethod
    def get_by_user(cls, session, user_id: int) -> List['ExpoToken']:
        return session.query(cls).filter_by(user_id=user_id).all()

    @classmethod
    def create(cls, session, expo_token: 'ExpoToken') -> Optional['ExpoToken']:
        if session.query(cls).filter_by(token=expo_token.token).one_or_none() is not None:
            return None
        session.add(expo_token)
        session.commit()
        session.refresh(expo_token)
        return expo_token

    def json(self, deep: bool=False) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'token': self.token
        }


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
    def add(cls, session, user_id: int, foodpreference: Union[int, List[int]]) -> Union['UserFoodPreference', List['UserFoodPreference']]:
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
    def update(cls, session, user_id: int, foodpreferences: Union[int, List[int]]):
        cls.delete(session, user_id)
        cls.add(session, user_id, foodpreferences)

    @classmethod
    def delete(cls, session, user_id: int):
        prefs = session.query(cls).filter_by(user_id=user_id)
        prefs.delete()

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
    def add(cls, session, user_id: int, code: str=None) -> 'UserVerification':
        assert user_id is not None
        code = code or cls.generate_code()
        verification = UserVerification(code, user_id)
        session.add(verification)
        session.commit()
        session.refresh(verification)
        return verification

    @classmethod
    def get_by_code(cls, session, code: str) -> Optional['UserVerification']:
        """Get entity by code"""
        return session.query(cls).filter_by(code=code).one_or_none()

    @classmethod
    def get_by_user(cls, session, user_id: int) -> Optional['UserVerification']:
        """Get entity by user"""
        return session.query(cls).filter_by(user_id=user_id).one_or_none()

    @classmethod
    def delete_by_code(cls, session, code: str) -> bool:
        """Delete instance"""
        success = session.query(cls).filter_by(code=code).delete()
        return success

    @classmethod
    def delete(cls, session, user_id: int) -> bool:
        """Delete instance"""
        success = session.query(cls).filter_by(user_id=user_id).delete()
        return success

    @classmethod
    def generate_code(cls, length: int=6) -> str:
        """Generate a new verification code"""
        chars = string.ascii_uppercase + string.digits
        code = random.choices(chars, k=length)
        return ''.join(code)


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
    def get_all_newest(cls) -> List['Event']:
        entities = db.session.query(cls).filter(cls.end_date > datetime.datetime.now()).order_by(cls.start_date).all()
        return entities

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
        self.time = time or datetime.datetime.utcnow()

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

    @classmethod
    def user_active_recommendations(cls, user_id: int) -> List['UserRecommendedEvent']:
        entities = db.session.query(cls).filter(cls.event.end_date > datetime.datetime.utcnow())
        return entities

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
    def delete(cls, session, id: str) -> bool:
        success = session.query(cls).filter_by(id=id).delete()
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


class Building(Base, Entity):
    __tablename__ = "Building"

    id = Column('id', BIGINT, primary_key=True, autoincrement=True)
    name = Column('name', VARCHAR(255), unique=True, nullable=False)
    latitude = Column('latitude', DECIMAL(10, 8), nullable=False)
    longitude = Column('longitude', DECIMAL(11, 8), nullable=False)

    def __init__(self, id: int=None, name: str=None, latitude: Decimal=None, longitude: Decimal=None):
        self.id = id
        self.name = name
        self.latitude = latitude
        self.longitude = longitude

    @classmethod
    def add(cls, name: str, latitude: Decimal, longitude: Decimal) -> 'Building':
        building = Building(name=name, latitude=latitude, longitude=longitude)
        db.session.add(building)
        db.session.commit()
        db.session.refresh(building)
        return building

    @classmethod
    def get_by_name(cls, name: str) -> Optional['Building']:
        return db.session.query(cls).filter_by(name=name).one_or_none()
