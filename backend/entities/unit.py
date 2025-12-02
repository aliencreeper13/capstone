"""
Base Unit class representing any game entity that can be created, upgraded, or destroyed.

Units include buildings, troops, and other game objects with properties like level,
size, effects, and job requirements.
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum

from ..core.constants import DESTRUCTION_WEALTH_COST_PER_UNIT_SIZE
from ..core.gameobject import GameObject, DataclassGameObject
from ..systems.data import ExpendableCityResources
from ..systems.effects import Effect
from ..systems.job_requirements import HasJobRequirementsMixin, JobRequirements

if TYPE_CHECKING:
    from .city import City


@dataclass
class BaseUnitAttributes:
    """Placeholder for unit attributes that may be expanded."""
    pass

class UnitCategory(Enum):
    """Enumeration of possible unit categories."""
    UNCATEGORIZED = "Uncategorized"
    MILITARY = "Military"
    ECONOMIC = "Economic"
    CIVILIAN = "Civilian"

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
        job_num_ticks: Number of ticks for job creation, upgrade, or destruction
    
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
    job_num_ticks: int
    category: UnitCategory = UnitCategory.UNCATEGORIZED
    
    def __init__(self, level=1, *args, **kwargs):
        """Initialize a unit at level `level`, inactive."""
        self._level: int = level
        self._active = False # units start inactive, meaning their effects don't apply
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

    @property
    def city(self) -> Optional[City]:
        """Get the city this unit belongs to (or None if unassigned)."""
        return self._city
    
    def upgrade(self, bonus_pct: float = 4):
        """
        Upgrade this unit to the next level.
        
        Increases level by 1 and applies level-specific effect bonuses.
        Each upgrade level provides a 20% bonus to the unit's effect.
        
        If unit is in a city, applies an upgrade bonus effect to the city.
        """
        self._level += 1
        
        # Apply upgrade bonus to city if unit is assigned to one
        if self._city is not None:
            # Create an upgrade bonus effect: 4% per level above 1
            # upgrade_bonus = (self._level - 1) * (bonus_pct / 100)
            upgrade_bonus = (bonus_pct / 100)
            
            # Scale the base effect by the upgrade bonus
            upgrade_effect = self.effect.get_upgraded(upgrade_bonus=upgrade_bonus)
            assert upgrade_effect.effect_id == self.effect.effect_id, "Upgraded effect must have same ID as base effect"
            # Add the upgrade effect to the city (replaces any previous upgrade for this unit, since effect_id is the same)
            self._city.add_effect(upgrade_effect)

            # assign the upgraded effect to the unit's effect for future upgrades
            self.effect = upgrade_effect

    @property
    def level(self) -> int:
        """Get current unit level."""
        return self._level
    