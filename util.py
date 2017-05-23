import json
from typing import Any, Dict
from sqlalchemy.orm.attributes import InstrumentedAttribute


def json_dict(obj: object, allow_none: bool=False) -> Dict[str, Any]:
    """Convert object's properties to dictionary for json encoding
    Includes SQLAlchemy database columns
    Skips all properties beginning with underscore
    obj: object to get properties of
    allow_none: allow properties with 'None' value (default: False)
    return: dict({<Property>, <Value>})
    """
    assert obj is not None, 'Object must not be None'
    return dict({prop: obj.__getattribute__(prop)
        for prop, typ in vars(type(obj)).items()
        if not prop.startswith('_')
           and isinstance(typ, (property, InstrumentedAttribute))
           and (allow_none or obj.__getattribute__(prop) is not None)
    })


def json_esc(data: object, indent: int=4) -> str:
    """JSON encode data with indent"""
    return json.dumps(data, indent=indent).replace("</", "<\\/")