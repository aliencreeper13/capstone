from __future__ import annotations

from constants import DESTRUCTION_WEALTH_COST_PER_UNIT_SIZE
from data import ExpendableCityResources
from job_requirements import JobRequirements, HasJobRequirementsMixin
from effects import Effect
from unit import Unit

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from city import City


    

class Building(Unit):
    def __init__(self, name: str, size: int, effects: Effect, requirements: JobRequirements = JobRequirements(), description: str=""):
        super().__init__(name=name,
                         size=size,
                         effects=effects,
                         requirements=requirements,
                         description=description
                         )
        self._city: Optional[City] = None # indicates what city it is part of

    def set_city(self, city: City):
        self._city = city

    