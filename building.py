from __future__ import annotations

from constants import DESTRUCTION_WEALTH_COST_PER_UNIT_SIZE
from data import CityResources
from job_requirements import JobRequirements, HasJobRequirementsMixin
from effects import Effect
from unit import Unit

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from city import City


    

class Building(Unit, HasJobRequirementsMixin):
    def __init__(self, name: str, size: int, effects: Effect, requirements: JobRequirements = JobRequirements()):
        super().__init__(name=name,
                         size=size,
                         effects=effects,
                         )
        self._city: Optional[City] = None # indicates what city it is part of
        self._requirements: JobRequirements = requirements
    def set_city(self, city: City):
        self._city = city

    @property
    def destruction_wealth_cost(self) -> int:
        return self.size * DESTRUCTION_WEALTH_COST_PER_UNIT_SIZE
    
    @property
    def creation_job_requirements(self) -> JobRequirements:
        return self._requirements
    
    @property
    def destruction_job_requirements(self) -> JobRequirements:
        return JobRequirements(
            city_resources_level1=CityResources(
                wealth=self.destruction_wealth_cost
            )
        )