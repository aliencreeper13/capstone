"""
Building class representing urban structures within cities.

Buildings are units that provide passive effects, generate resources, or unlock
military capabilities. They take up space in a city and require resources/workers
to construct and maintain.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ..core.gameobject import GameObject, public_client_property
from ..core.constants import DESTRUCTION_WEALTH_COST_PER_UNIT_SIZE
from ..systems.data import ExpendableCityResources
from ..systems.job_requirements import JobRequirements, HasJobRequirementsMixin
from ..systems.effects import Effect
from .unit import Unit

if TYPE_CHECKING:
    from .city import City
    from .empire import Empire


class Building(Unit):
    """
    Base class for all buildings in a city.
    
    Buildings are urban structures that occupy space and provide passive effects.
    They are owned by a city but have allegiance to the empire that controls
    the city.
    
    Instance attributes:
        _city: City this building is located in
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize building and set city reference."""
        super().__init__(*args, **kwargs)
        self._city: Optional[City] = None

    @public_client_property
    def allegiance(self) -> Optional[Empire]:
        """
        Get the empire this building is allegiant to.
        
        Returns the allegiance of the city this building is in,
        or None if building is not assigned to a city.
        """
        if self._city is None:
            return None
        return self._city.allegiance