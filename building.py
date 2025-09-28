from __future__ import annotations

from building_requirements import BuildingRequirements
from effects import Effects
from unit import Unit

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from city import City


    

class Building(Unit):
    def __init__(self, name: str, size: int, effects: Effects, requirements: BuildingRequirements = BuildingRequirements()):
        super().__init__(name=name,
                         size=size,
                         effects=effects)
        self._city: Optional[City] = None # indicates what city it is part of
        self._requirements: BuildingRequirements = requirements
    def set_city(self, city: City):
        self._city = city
    
    @property
    def requirements(self) -> BuildingRequirements:
        return self._requirements