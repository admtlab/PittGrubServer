import logging
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import NullPool

from .base import Entity, ReferralStatus, UserStatus, health_check
from .default import DEFAULTS
from .schema import (
    AccessToken, Building, Event, EventFoodPreference, EventImage, EventType,
    EventTypeRel, FoodPreference, User, UserAcceptedEvent, UserVerification,
    UserCheckedInEvent, UserFoodPreference, UserRecommendedEvent, UserReferral
)

# database session
# initialized by init()
session = None

# database testing values
# insert when 'generate' flag is True
TEST_DATA = dict({
    'User': [
        (1, 'xyz@pitt.edu', '12345', UserStatus.ACCEPTED, True, False, True, 0),
        (2, 'abc@pitt.edu', '12345', UserStatus.ACCEPTED, True, False, False, 0)
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
        for i in values:
            session.merge(cls(*i))
        session.commit()

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
    global session
    engine = create_engine(f"mysql+pymysql://{username}:{password}"
                           f"@{url}/{database}{params}",
                           convert_unicode=True, echo=echo,
                           pool_recycle=1800)
    session = scoped_session(sessionmaker(bind=engine))
    print('Inserting default data')
    __bulk_insert(engine, DEFAULTS) # add default data
    if generate: 
        print('Generating test data')
        __bulk_insert(engine, TEST_DATA)    # add test data if generate flag is set to true
