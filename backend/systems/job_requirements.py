"""
Job system requirements and specifications.

Defines the requirements for jobs (building creation/upgrade/destruction, unit creation, etc.)
including resources, workers, and contingencies on other units/buildings.
"""

from __future__ import annotations

from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from math import ceil
from typing import TYPE_CHECKING, Optional

from ..core.gameobject import GameObject, DataclassGameObject
from .data import ExpendableCityResources

if TYPE_CHECKING:
    from ..entities.unit import Unit


@dataclass
class ContingentOnInfo(DataclassGameObject):
    """
    Specifies that a job depends on a particular unit type existing at required level.
    
    Attributes:
        unit_class: The unit/building type required
        minimum_level_needed: Minimum level of that unit/building required
    """
    unit_class: type[Unit]
    minimum_level_needed: int = 1


@dataclass
class JobRequirements(DataclassGameObject):
    """
    Specifies the requirements and costs for a job (building/unit creation or upgrade).
    
    Requirements scale exponentially with job level using an exponent multiplier.
    This creates increasing costs for higher-level upgrades.
    
    Attributes:
        knowledge_level1: Knowledge cost at level 1 (floating point for precision)
        expendable_city_resources_level1: Resource costs at level 1
        workers_needed_level1: Workers required at level 1
        specific_units_contingent_on: Specific unit instances that must be active
        unit_types_contingent_on: Unit types that must exist in the city
        max_per_city: Maximum count allowed in a single city (None = unlimited)
        exponent: Scaling factor for higher levels (1.05 = 5% increase per level)
    """

    knowledge_level1: float = 0.0
    expendable_city_resources_level1: ExpendableCityResources = field(
        default_factory=ExpendableCityResources
    )
    workers_needed_level1: int = 0
    specific_units_contingent_on: list[Unit] = field(default_factory=list)
    unit_types_contingent_on: list[ContingentOnInfo] = field(default_factory=list)
    max_per_city: Optional[int] = None
    exponent: float = 1.05

    def city_resources(self, level: int) -> ExpendableCityResources:
        """
        Calculate resource requirements for a given job level.
        
        Args:
            level: The job level (1-based)
            
        Returns:
            ExpendableCityResources with costs scaled by exponent
        """
        return ExpendableCityResources(
            food=ceil(self.expendable_city_resources_level1.food * self.exponent**(level - 1)),
            timber=ceil(self.expendable_city_resources_level1.timber * self.exponent**(level - 1)),
            wealth=ceil(self.expendable_city_resources_level1.wealth * self.exponent**(level - 1)),
            metal=ceil(self.expendable_city_resources_level1.metal * self.exponent**(level - 1))
        )
    
    def workers_needed(self, level: int) -> int:
        """
        Calculate worker requirement for a given job level.
        
        Args:
            level: The job level (1-based)
            
        Returns:
            Number of workers needed, scaled by exponent
        """
        return ceil(self.workers_needed_level1 * self.exponent**(level - 1))

    def food(self, level: int) -> float:
        """Get food requirement for level."""
        return self.city_resources(level=level).food
    
    def timber(self, level: int) -> float:
        """Get timber requirement for level."""
        return self.city_resources(level=level).timber
    
    def wealth(self, level: int) -> float:
        """Get wealth requirement for level."""
        return self.city_resources(level=level).wealth
    
    def metal(self, level: int) -> float:
        """Get metal requirement for level."""
        return self.city_resources(level=level).metal
    
    def knowledge(self, level: int) -> float:
        """Get knowledge requirement for level (floating point for precision)."""
        return self.knowledge_level1 * self.exponent**(level - 1)


class HasJobRequirementsMixin(ABC):
    """
    Mixin for objects that have creation and destruction job requirements.
    
    Used for buildings and units that can be created and destroyed through jobs.
    """
    
    @property
    @abstractmethod
    def creation_job_requirements(self) -> JobRequirements:
        """Get the requirements for creating this object."""
        pass
    
    @property
    @abstractmethod
    def destruction_job_requirements(self) -> JobRequirements:
        """Get the requirements for destroying this object."""
        pass