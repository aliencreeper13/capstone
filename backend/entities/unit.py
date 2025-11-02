"""
Base Unit class representing any game entity that can be created, upgraded, or destroyed.

Units include buildings, troops, and other game objects with properties like level,
size, effects, and job requirements.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..core.constants import DESTRUCTION_WEALTH_COST_PER_UNIT_SIZE
from ..core.gameobject import GameObject
from ..systems.data import ExpendableCityResources
from ..systems.effects import Effect
from ..systems.job_requirements import HasJobRequirementsMixin, JobRequirements

if TYPE_CHECKING:
    from .city import City


@dataclass
class BaseUnitAttributes:
    """Placeholder for unit attributes that may be expanded."""
    pass


class Unit(GameObject, HasJobRequirementsMixin, ABC):
    """
    Base class for all game units (buildings, troops, etc.).
    
    Units have levels, sizes, effects, and requirements. They exist within cities
    and can be created, upgraded, or destroyed through jobs.
    
    Class attributes (must be overridden by subclasses):
        name: Display name of the unit type
        size: Space taken up in city (0-5+)
        effect: Passive effect when unit is active
        job_requirements: Requirements for creating new units
        description: Flavor text describing the unit
    
    Instance attributes:
        _level: Current upgrade level (starts at 1)
        _active: Whether unit is currently functioning
        _city: City this unit belongs to
    """
    
    # Must be set by subclasses
    name: str
    size: int
    effect: Effect
    job_requirements: JobRequirements
    description: str
    
    def __init__(self, *args, **kwargs):
        """Initialize a unit at level 1, inactive."""
        self._level: int = 1
        self._active = False
        self._city: Optional[City] = None

    def set_active(self):
        """Activate this unit so its effects apply."""
        self._active = True

    def set_inactive(self):
        """Deactivate this unit so its effects don't apply."""
        self._active = False

    def is_active(self) -> bool:
        """Return True if unit is currently active."""
        return self._active
    
    def set_city(self, city: City):
        """Assign this unit to a city."""
        self._city = city

    @classmethod
    def destruction_wealth_cost(cls, level: int) -> int:
        """
        Calculate wealth cost to destroy a unit of given level.
        
        Cost depends on unit size (larger units cost more to destroy).
        
        Args:
            level: Unit level (affects calculation)
            
        Returns:
            Wealth cost to destroy
        """
        return cls.size * DESTRUCTION_WEALTH_COST_PER_UNIT_SIZE
    
    @property
    def creation_job_requirements(self) -> JobRequirements:
        """Get requirements for creating this unit type."""
        return self.job_requirements

    @property
    def destruction_job_requirements(self) -> JobRequirements:
        """
        Get requirements for destroying this specific unit instance.
        
        Destruction only costs wealth, scaled by unit size and current level.
        """
        return JobRequirements(
            expendable_city_resources_level1=ExpendableCityResources(
                wealth=self.destruction_wealth_cost(level=self._level)
            )
        )
    
    def upgrade(self):
        """
        Upgrade this unit to the next level.
        
        Increases level by 1 and applies level-specific effect bonuses.
        Each upgrade level provides a 20% bonus to the unit's effect.
        
        If unit is in a city, applies an upgrade bonus effect to the city.
        """
        self._level += 1
        
        # Apply upgrade bonus to city if unit is assigned to one
        if self._city is not None:
            # Create an upgrade bonus effect: 20% per level above 1
            upgrade_bonus = (self._level - 1) * 0.20
            
            # Scale the base effect by the upgrade bonus
            upgrade_effect = Effect(
                duration_in_ticks=0,  # Indefinite
                expendable_city_resources_per_tick=self.effect.expendable_city_resources_per_tick * upgrade_bonus,
                expendable_city_resource_capacities_offered=self.effect.expendable_city_resource_capacities_offered * upgrade_bonus,
                raw_morale_per_tick=self.effect.raw_morale_per_tick * upgrade_bonus,
                city_base_defense_offered=self.effect.city_base_defense_offered * upgrade_bonus,
                city_base_protection_offered=self.effect.city_base_protection_offered * upgrade_bonus,
                efficiency_per_tick=self.effect.efficiency_per_tick * upgrade_bonus,
                # Use a special effect ID that ties this upgrade to this specific unit instance
                effect_id=hash(f"upgrade_{id(self)}")
            )
            
            # Add the upgrade effect to the city (replaces any previous upgrade for this unit)
            self._city.add_effect(upgrade_effect)

    @property
    def level(self) -> int:
        """Get current unit level."""
        return self._level