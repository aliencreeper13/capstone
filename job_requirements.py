from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from math import ceil
from data import CityResources

@dataclass
class JobRequirements:

    knowledge_level1: int = 0
    city_resources_level1: CityResources = CityResources.empty_resources()

    exponent: float = 1.05

    def city_resources(self, level: int) -> CityResources:
        return CityResources(
            food=ceil(self.city_resources_level1.food * self.exponent**(level - 1)),
            timber=ceil(self.city_resources_level1.timber * self.exponent**(level - 1)),
            wealth=ceil(self.city_resources_level1.wealth * self.exponent**(level - 1)),
            metal=ceil(self.city_resources_level1.metal * self.exponent**(level - 1))
        )
    

    def food(self, level: int) -> int:
        return self.city_resources(level=level).food
    
    def timber(self, level: int) -> int:
        return self.city_resources(level=level).timber
    
    def wealth(self, level: int) -> int:
        return self.city_resources(level=level).wealth
    
    def metal(self, level: int) -> int:
        return self.city_resources(level=level).metal
    
    def knowledge(self, level: int) -> int:
        return ceil(self.knowledge_level1 * self.exponent**(level - 1))
    
class HasJobRequirementsMixin:
    @property
    @abstractmethod
    def creation_job_requirements(self) -> JobRequirements:
        pass
    
    @property
    @abstractmethod
    def destruction_job_requirements(self) -> JobRequirements:
        pass
