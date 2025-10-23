from __future__ import annotations

from constants import DESTRUCTION_WEALTH_COST_PER_UNIT_SIZE
from data import ExpendableCityResources
from job_requirements import JobRequirements, HasJobRequirementsMixin
from effects import Effect
from unit import Unit

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from city import City
    from empire import Empire


    

class Building(Unit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._city: Optional[City] = None # indicates what city it is part of

    @property
    def allegiance(self) -> Empire | None:
        if self._city is None:
            return None
        return self._city.allegiance

    

    