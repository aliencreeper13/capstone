import json
from typing import Any

class client_property(property):
    def __init__(self, fget = ..., fset = ..., fdel = ..., doc = ...):
        super().__init__(fget, fset, fdel, doc)

def client(prop: property):
    """Marks a property as client-exposed."""
    prop._is_client_exposed = True
    return prop

class GameObject:
    def to_client_dict(self) -> dict[str, Any]:
        data = {}
        # Go through all attributes on the class
        for attr_name in dir(self):
            attr = getattr(type(self), attr_name, None)
            if isinstance(attr, client_property): # and getattr(attr, "_is_client_exposed", False):
                value = getattr(self, attr_name)

                # Recursively serialize GameObjects
                if isinstance(value, GameObject):
                    value = value.to_client_dict()
                elif isinstance(value, list) and all(isinstance(v, GameObject) for v in value):
                    value = [v.to_client_dict() for v in value]

                data[attr_name] = value
        return data

    def to_client_json(self) -> str:
        return json.dumps(self.to_client_dict(), indent=2)