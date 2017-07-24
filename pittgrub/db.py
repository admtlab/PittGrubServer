import json
import sys
import datetime
from typing import Any, Dict, Optional, List, Tuple, Union, TypeVar
try:
    import tornado
except ModuleNotFoundError:
    # DB10 fix
    sys.path.insert(0, '/afs/cs.pitt.edu/projects/admt/web/sites/db10/beacons/python/site-packages/')
finally:
    from passlib.hash import bcrypt
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
        (1, 'xyz@pitt.edu', '12345', True, False, 'ExponentPushToken[NsV1cTOVuOvp-GCbk_HVtM]'),
        (2, 'abc@pitt.edu', '12345')
    ],
    'UserFoodPreference': [
        (1, 1),
        (1, 3),
        (2, 4),
    ],
    'Event': [
        (1, 1, 'Sodexo', 'Free pizza',
         datetime.datetime.now()+datetime.timedelta(minutes=2),
         datetime.datetime.now()+datetime.timedelta(hours=2),
         'Come try out our new pizza toppings!',
         None, '3990 Fifth Ave.', 'Ground floor of Towers'),
        (2, 1, 'Sodexo', 'Coffee hour',
         datetime.datetime.now()+datetime.timedelta(minutes=2),
         datetime.datetime.now()+datetime.timedelta(hours=1, minutes=2),
         'Come stop by every week for a free coffee!',
         None, '3959 Fifth Ave.', 'William Pitt Union patio'),
        (3, 1, 'Graduate and Student Government', 'Donut mixer',
         datetime.datetime.now()+datetime.timedelta(days=3),
         datetime.datetime.now()+datetime.timedelta(days=3, hours=2),
         'Get to know your student government officers over donuts',
         None, '3907 Forbes Ave.', 'Dunkin Donuts'),
    ],
    'EventFoodPreference': [
        (1, 4),
        (2, 1),
        (2, 2),
        (2, 3),
        (2, 4),
        (3, 3),
    ],
    'UserAcceptedEvent': [
        (1, 1),
        (1, 2),
        (2, 1),
        (3, 1),
    ],
    'UserRecommendedEvent': [
        (2, 2),
    ],
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
    def get_all(cls, filters: List[Tuple[str, Any]]=None,
                orders: List[str]=None) -> List[E]:
        # query = session.query(cls)
        # if filters:
        #     query = query.filter_by(**)
        # if orders:
        #     query = query.order_by(*orders)
        # print(f'session query: {session.query(cls)}')
        return session.query(cls).all()

    @classmethod
    def get_by_id(cls, id: int) -> Optional[E]:
        return session.query(cls).get(id)

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
        self.expo_token = expo_token;

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

    @classmethod
    def get_by_email(cls, email: str) -> Optional['User']:
        return session.query(cls).filter(User.email == email).one_or_none()

    @classmethod
    def verify(cls, email: str, password: str) -> bool:
        user = User.get_by_email(email)
        if user is None:
            return False
        return bcrypt.verify(password, user.password)

    @classmethod
    def add_expo_token(cls, id: int, expo_token: str) -> bool:
        try:
            user = User.get_by_id(id)
            user.expo_token = expo_token
            session.commit()
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
                session.add(user_foodpreference)
                user_foodpreferences.append(user_foodpreference)
        else:
            user_foodpreferences = UserFoodPreference(user_id, foodpreference)
            session.add(user_foodpreference)
        session.commit()
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
        session.add(event)
        session.commit()
        session.refresh(event)
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
        return session.query(cls).get([event_id, foodpreference_id])

    @classmethod
    def add(cls, event_id: int, foodpreference: Union[int, List[int]]) -> Union['EventFoodPreference', List['EventFoodPreference']]:

        if isinstance(foodpreference, list):
            event_foodpreferences = []
            for fp in foodpreference:
                event_foodpreference = EventFoodPreference.get_by_id(event_id, fp)
                if not event_foodpreference:
                    event_foodpreference = EventFoodPreference(event_id, fp)
                    session.add(event_foodpreference)
                event_foodpreferences.append(event_foodpreference)
        else:
            event_foodpreferences = EventFoodPreference.get_by_id(event_id, foodpreference)
            if not event_foodpreferences:
                event_foodpreferences = EventFoodPreference(event_id, foodpreference)
                session.add(event_foodpreferences)
        session.commit()
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

    event = relationship(Event, backref=backref('_event_recommended_users'))
    user = relationship(User, backref=backref('_user_recommended_events'))

    def __init__(self, event_id: int, user_id: int):
        self.event_id = event_id
        self.user_id = user_id

    @classmethod
    def find_by_id(cls, event_id: int, user_id: int) -> Optional['UserRecommendedEvent']:
        return session.query(cls).get([event_id, user_id])

    def json(cls, deep: bool=False) -> Dict[str, Any]:
        if deep:
            return {
                'event': cls.event.json(deep),
                'user': cls.user.json(False)
            }
        else:
            return {
                'event': cls.event_id,
                'user': cls.user_id
            }


class UserAcceptedEvent(Base):
    __tablename__ = 'UserAcceptedEvent'

    event_id = Column('event_id', BIGINT, ForeignKey('Event.id'), primary_key=True)
    user_id = Column('user_id', BIGINT, ForeignKey('User.id'), primary_key=True)

    event = relationship(Event, backref=backref('_event_accepted_users'))
    user = relationship(User, backref=backref('_user_accepted_events'))

    def __init__(self, event_id: int, user_id: int):
        self.event_id = event_id
        self.user_id = user_id

    @classmethod
    def find_by_id(cls, event_id: int, user_id: int) -> Optional['UserAcceptedEvent']:
        return session.query(cls).get([event_id, user_id])

    @classmethod
    def add(cls, event_id: int, user_id: int) -> 'UserAcceptedEvent':

        user_accepted_event = UserAcceptedEvent.find_by_id(event_id, user_id)
        if not user_accepted_event:
            user_accepted_event = UserAcceptedEvent(event_id, user_id)
            session.add(user_accepted_event)
            session.commit()
        return user_accepted_event

    def json(cls, deep: bool=False) -> Dict[str, Any]:
        if deep:
            return {
                'event': cls.event.json(deep),
                'user': cls.user.json(False)
            }
        else:
            return {
                'event': cls.event_id,
                'user': cls.user_id,
            }


class UserCheckedInEvent(Base):
    __tablename__ = 'UserCheckedInEvent'

    event_id = Column('event_id', BIGINT, ForeignKey('Event.id'), primary_key=True)
    user_id = Column('user_id', BIGINT, ForeignKey('User.id'), primary_key=True)

    event = relationship(Event, backref=backref('_event_checkedin_users'))
    user = relationship(User, backref=backref('_user_checkedin_events'))

    def __init__(self, event_id: int, user_id: int):
        self.event_id = event_id
        self.user_id = user_id

    @classmethod
    def find_by_id(cls, event_id: int, user_id: int) -> Optional['UserCheckedInEvent']:
        return session.query(cls).get([event_id, user_id])

    def json(cls, deep: bool=False) -> Dict[str, Any]:
        if deep:
            return {
                'event': cls.event.json(deep),
                'user': cls.user.json(False)
            }
        else:
            return {
                'event': cls.event_id,
                'user': cls.user_id
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
