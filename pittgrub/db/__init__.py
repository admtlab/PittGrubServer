import logging
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from .base import Entity, ReferralStatus, UserStatus, health_check
from .default import DEFAULTS
from .schema import (
    AccessToken, Building, Event, EventFoodPreference, EventImage, EventType,
    EventTypeRel, FoodPreference, Role, User, UserAcceptedEvent,
    UserCheckedInEvent, UserFoodPreference, UserHostRequest,
    UserRecommendedEvent, UserReferral, UserRole, UserVerification,
)

# database sessionmaker
# initialized by init()
_Session = None

# database testing values
# insert when 'generate' flag is True
TEST_DATA = dict({
    'User': [
        (1, 'xyz@pitt.edu', '12345', UserStatus.ACCEPTED, "XYZ Tester", True, False, True, 0),
        (2, 'abc@pitt.edu', '12345', UserStatus.ACCEPTED, "ABC Tester", True, False, False, 0)
    ],
    'UserFoodPreference': [
        (1, 1),
        (1, 3),
        (2, 4),
    ],
    'Event': [
        (1, 1, 'Sodexo', 'Free pizza',
         datetime.now()+timedelta(minutes=2),
         datetime.now()+timedelta(hours=2),
         'Come try out our new pizza toppings!',
         None, '3990 Fifth Ave.', 'Ground floor of Towers'),
        (2, 1, 'Sodexo', 'Coffee hour',
         datetime.now()+timedelta(minutes=2),
         datetime.now()+timedelta(hours=1, minutes=2),
         'Come stop by every week for a free coffee!',
         None, '3959 Fifth Ave.', 'William Pitt Union patio'),
        (3, 1, 'Graduate and Student Government', 'Donut mixer',
         datetime.now()+timedelta(days=3),
         datetime.now()+timedelta(days=3, hours=2),
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
        (1, 1, datetime.utcnow()),
        (1, 2, datetime.utcnow()),
        (2, 1, datetime.utcnow()),
        (3, 1, datetime.utcnow()),
    ],
    'UserRecommendedEvent': [
        (2, 2),
    ],
})


def __bulk_insert(engine, data: Dict[str, List[Tuple[Any]]]):
    schema.Base.metadata.create_all(bind=engine)
    for entity, values in data.items():
        # get class of entity
        cls = getattr(sys.modules[__name__], entity)
        # merge values
        # this avoids duplicate errors
        with session_scope() as session:
            for i in values:
                session.merge(cls(*i))


@contextmanager
def session_scope():
    """
    Provides a transactional scope around a series of operations
    http://docs.sqlalchemy.org/en/latest/orm/session_basics.html
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def get_session():
    """
    Return new SQLAlchemy session from sessionmaker
    """
    global _Session
    return _Session()


def init(username: str, password: str, url: str, database: str,
         params: str, echo: bool=False, generate: bool=False):
    """Initialize database

    :username: username
    :password: user's password
    :url:      database url
    :database: database name
    :params:   parameters
    :echo:     log commands
    :generate: generate tables dynamically
    """
    global _Session
    engine = create_engine(f"mysql+pymysql://{username}:{password}"
                           f"@{url}/{database}{params}",
                           convert_unicode=True, echo=echo,
                           pool_recycle=1800)
    _Session = sessionmaker(bind=engine)
    print('Inserting default data')
    __bulk_insert(engine, DEFAULTS) # add default data
    if generate:
        print('Generating test data')
        __bulk_insert(engine, TEST_DATA)    # add test data if generate flag is set to true
