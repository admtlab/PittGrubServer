from typing import Optional

from db import Property, session_scope


def get_property(name: str) -> Optional[str]:
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
