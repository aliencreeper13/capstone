from __future__ import annotations
from typing import Optional
from constants import DESTRUCTION_WEALTH_COST_PER_UNIT_SIZE
from data import ExpendableCityResources
from effects import Effect

from gameobject import GameObject
from job_requirements import HasJobRequirementsMixin, JobRequirements

class Unit(GameObject, HasJobRequirementsMixin):
    def __init__(self,  name: str, size: int = 1, effects: Effect = Effect, job_requirements: JobRequirements = JobRequirements(), description: str = ""):
        self.name: str = name
        self._size: int = size
        self._level: int = 1
        self._effects: Effect = effects
        self._active = False

        self._job_requirements = job_requirements

        self._description: str = description

    def set_active(self):
        self._active = True

    def set_inactive(self):
        self._active = False


    def is_active(self):
        return self._active

    @property
    def size(self) -> int:
        return self._size
    
    @property
    def effects(self) -> Effect:
        return self._effects
    
    @property
    def level(self) -> int:
        return self._level
    
    @property
    def destruction_wealth_cost(self) -> int:
        return self.size * DESTRUCTION_WEALTH_COST_PER_UNIT_SIZE
    
    @property
    def creation_job_requirements(self) -> JobRequirements:
        return self._requirements
    
    @property
    def destruction_job_requirements(self) -> JobRequirements:
        return JobRequirements(
            city_resources_level1=ExpendableCityResources(
                wealth=self.destruction_wealth_cost
            )
        )
    
    def upgrade(self):
        # todo: upgrade effects as well (soon to be implemented)
        self._level += 1

    @property
    def description(self) -> str:
        return self._description
    
