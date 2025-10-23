from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass

from constants import DESTRUCTION_WEALTH_COST_PER_UNIT_SIZE
from data import ExpendableCityResources
from effects import Effect

from gameobject import GameObject
from job_requirements import HasJobRequirementsMixin, JobRequirements
from abc import abstractproperty, abstractmethod, ABC

if TYPE_CHECKING:
    from city import City

@dataclass
class BaseUnitAttributes:
    pass

class Unit(GameObject, HasJobRequirementsMixin, ABC):
    # these are class attributes which must be overridden
    name: str
    size: int
    effect: Effect
    job_requirements: JobRequirements  # job requirements for *creation*
    description: str
    def __init__(self, *args, **kwargs):
        self._name: str = self.name
        self._size: int = self.size
        self._level: int = 1
        self._effects: Effect = self.effect
        self._active = False

        self._job_requirements = self.job_requirements

        self._description: str = self.description

        self._city: Optional[City] = None

    def set_active(self):
        self._active = True

    def set_inactive(self):
        self._active = False


    def is_active(self):
        return self._active
    
    def set_city(self, city: City):
        self._city = city

    @classmethod
    def destruction_wealth_cost(cls, level: int) -> int:
        return cls.size * DESTRUCTION_WEALTH_COST_PER_UNIT_SIZE
    
    @property
    def creation_job_requirements(self) -> JobRequirements:
        return self._job_requirements

    def destruction_job_requirements(self) -> JobRequirements:
        return JobRequirements(
            city_resources_level1=ExpendableCityResources(
                wealth=self.destruction_wealth_cost(level=self._level)
            )
        )
    
    def upgrade(self):
        # todo: upgrade effects as well (soon to be implemented)
        self._level += 1
        print(f"{self} just upgraded to {self._level}!!!")

    @property
    def level(self) -> int:
        return self._level


    
