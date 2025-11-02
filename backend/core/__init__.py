"""
Core package: Foundational classes, constants, and utilities.

This package contains the foundational components that all other packages depend on:

Modules:
    - constants: Game balance parameters and configuration
    - exceptions: Custom exceptions used throughout the game
    - gameobject: Base GameObject class and mixins
    - engine_utils: Core utility functions for calculations
"""

from . import constants
from . import exceptions
from . import gameobject
from . import engine_utils

from .constants import *
from .exceptions import *
from .gameobject import GameObject, HasAllegianceMixin, public_client_property, private_client_property
from .engine_utils import *

__all__ = [
    "constants",
    "exceptions",
    "gameobject",
    "engine_utils",
    "GameObject",
    "HasAllegianceMixin",
    "public_client_property",
    "private_client_property",
]