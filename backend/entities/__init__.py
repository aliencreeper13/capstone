"""
Entities package containing all game entity classes.

This package provides the core game entities:
- Unit: Base class for units and buildings
- Building: Urban structures that produce resources or provide capabilities
- City: Population centers that manage resources, buildings, and armies
- Empire: Player empires that control multiple cities
- Ideology: Political systems affecting empire-wide mechanics
- Army: Military forces composed of units
"""

# Import order matters here due to circular dependencies
# Use relative imports to be explicit about package structure

from .unit import Unit, BaseUnitAttributes
from .building import Building
from .ideology import (
    Ideology,
    NeutralIdeology,
    Monarchy,
    Republic,
    Communism,
    Dictatorship,
    Anarchy,
    Socialism,
    Theocracy,
)
from .army import Army, Troop
from .city import City
from .empire import Empire, EmptyEmpire

__all__ = [
    "Unit",
    "BaseUnitAttributes",
    "Building",
    "Ideology",
    "NeutralIdeology",
    "Monarchy",
    "Republic",
    "Communism",
    "Dictatorship",
    "Anarchy",
    "Socialism",
    "Theocracy",
    "Army",
    "Troop",
    "City",
    "Empire",
    "EmptyEmpire",
]