from __future__ import annotations

from job_requirements import JobRequirements, HasJobRequirementsMixin
from effects import Effects
from unit import Unit

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from city import City


    

class Building(Unit, HasJobRequirementsMixin):
    def __init__(self, name: str, size: int, effects: Effects, requirements: JobRequirements = JobRequirements()):
        super().__init__(name=name,
                         size=size,
                         effects=effects,
                         )
        self._city: Optional[City] = None # indicates what city it is part of
        self._requirements: JobRequirements = requirements
    def set_city(self, city: City):
        self._city = city
    
    @property
    def job_requirements(self) -> JobRequirements:
        return self._requirements