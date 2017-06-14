import json
import sys
from typing import Any, Dict
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.ext.associationproxy import AssociationProxy, _AssociationList
import inflect
p = inflect.engine()

def json_dict(obj: object, allow_none: bool=False) -> Dict[str, Any]:
    """Convert object's properties to dictionary for json encoding
    Includes SQLAlchemy database columns
    Skips all properties beginning with underscore
    obj: object to get properties of
    allow_none: allow properties with 'None' value (default: False)
    return: dict({<Property>, <Value>})
    """
    assert obj is not None, 'Object must not be None'
    properties = dict()
    try:
        print(f'obj: {obj}')
        print(f'type: {type(obj)}')
        print(f'vars: {vars(type(obj))}')
    except:
        pass
    for prop, typ in vars(type(obj)).items():
        val = obj.__getattribute__(prop)
        if not prop.startswith('_') and (allow_none or val is not None):
            if isinstance(typ, (property, InstrumentedAttribute)):
                print(f'prop: {prop}')
                print(f'val: {val}')
                properties[prop] = val
            elif isinstance(typ, _AssociationList):
                properties[prop] = {'test': [json_dict(v) for v in val]}
    return properties
    # return dict({prop: obj.__getattribute__(prop)
    #     for prop, typ in vars(type(obj)).items()
    #     if not prop.startswith('_')
    #        and isinstance(typ, (property, InstrumentedAttribute))
    #        and (allow_none or obj.__getattribute__(prop) is not None)
    # })


def json_esc(data: object, indent: int=2) -> str:
    """JSON encode data with indent"""
    return json.dumps(data, indent=indent).replace("</", "<\\/")
