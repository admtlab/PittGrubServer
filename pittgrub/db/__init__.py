import sys
from datetime import datetime, timedelta

from .schema import (
    AccessToken, Event, EventFoodPreference, EventImage, EventType,
    EventTypeRel, FoodPreference, User, UserAcceptedEvent, UserReferral,
    UserActivation, UserCheckedInEvent, UserFoodPreference, UserRecommendedEvent
)
from .base import Entity, ReferralStatus, UserStatus

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker
except ModuleNotFoundError:
    # DB10 fix
    sys.path.insert(0, '/afs/cs.pitt.edu/projects/admt/web/sites/db10/beacons/python/site-packages/')

    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker


# database session
# initialized by init()
session = None

# database default values
DEFAULTS = dict({
    'FoodPreference': [
        (1, 'Gluten Free',
            "No gluten, which is found in wheat, barley, rye, and oat."),
        (2, 'Dairy Free',
            "No dairy, which includes any items made with cow's milk. This "
            "includes milk, butter, cheese, and cream."),
        (3, 'Vegetarian',
            "No meat, which includes red meat, poultry, and seafood."),
        (4, 'Vegan',
            "No animal products, including, but not limited to, dairy "
            "(milk products), eggs, meat (red meat, poultry, and seafood"
            "), and honey."),
    ],
    'User': [
        (1, 'xyz@pitt.edu', '12345', UserStatus.VERIFIED, True, False, True, 0),
        (2, 'abc@pitt.edu', '12345', UserStatus.VERIFIED, True, False, False, 0)
    ],
    'AccessToken': [
        # ('4ec1f791944d4c319822bd27f151f38d', 1, datetime.now()+timedelta(days=7)),
        # ('d33318c4a9f1459cb4f5789c208e0e78', 2, datetime.now()+timedelta(days=7)),
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
        schema.Base.metadata.create_all(bind=engine)
        # add default rows
        for entity, values in DEFAULTS.items():
            # get class of entity
            cls = getattr(sys.modules[__name__], entity)
            # merge values
            # this avoids duplicate errors
            for i in values:
                session.merge(cls(*i))
            session.commit()
