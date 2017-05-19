from typing import Any, Dict

def property_dict(obj: object, allow_none: bool=False) -> Dict[str, Any]:
    """Convert object's properties to dictionary for json encoding
    Skips properties beginning with underscore
    obj: object to get properties of
    allow_none: allow properties with 'None' value (default: False)
    return: dict({<Property_Name>, <Value>})
    """
    assert obj is not None, 'Object must not be None'
    return dict({prop: obj.__getattribute__(prop)
        for prop, typ in vars(type(obj)).items()
        if not prop.startswith('_')
           and isinstance(typ, property)
           and (allow_none or obj.__getattribute__(prop) is not None)
    })
