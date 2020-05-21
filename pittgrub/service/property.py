import logging
from typing import Optional
from db import Property, session_scope


__property_cache = {}


def init_cache():
    with session_scope() as session:
        properties = Property.get_cacheable(session)
        for prop in properties:
            logging.debug(f'property: {prop.name}')
            __property_cache[prop.name] = prop.value
    logging.debug(f'initialized: {__property_cache}')


def get_property(name: str) -> Optional[str]:
    if name in __property_cache:
        return __property_cache[name]

    with session_scope() as session:
        prop = Property.get_by_name(session, name)
        if prop is not None:
            return prop.value
        return None


def set_property(name: str, value):
    with session_scope() as session:
        prop = Property.get_by_name(session, name)
        prop.value = str(value)
        session.merge(prop)
