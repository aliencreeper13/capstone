from __future__ import annotations

import json
from typing import Any, Optional, TYPE_CHECKING
if TYPE_CHECKING:
    from engine.empire import Empire

class client_property(property):
    def __init__(self, fget = ..., fset = ..., fdel = ..., doc = ...):
        super().__init__(fget, fset, fdel, doc)

class public_client_property(client_property):
    """Properties accessible by every player in the game"""
    pass

class private_client_property(client_property):
    """Properties accessible only to authorized players (e.g. city data only accessible to city owner)"""
    pass

class GameObject:
    def to_client_dict(self, viewer: Optional[Empire]) -> dict[str, Any]:
        data = {}
        # Go through all attributes on the class
        for attr_name in dir(self):
            attr = getattr(type(self), attr_name, None)
            if isinstance(attr, client_property):
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