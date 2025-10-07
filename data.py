from __future__ import annotations

from dataclasses import dataclass, field

from gameobject import GameObject

@dataclass
class ExpendableCityResources(GameObject):
    food: float = 0.0
    timber: float = 0.0
    wealth: float = 0.0
    metal: float = 0.0

    @classmethod
    def empty_resources(cls):
        return ExpendableCityResources(
            food=0,
            timber=0,
            wealth=0,
            metal=0
        )
    
    def __neg__(self) -> ExpendableCityResources:
        return ExpendableCityResources(
            food=-self.food,
            timber=-self.timber,
            wealth=-self.wealth,
            metal=-self.metal
        )

@dataclass
class Population(GameObject):
    ages: list[int] = field(default_factory=lambda: [0]*100) # the nth index corresponds to the number of people who are n years old
    ages_can_work: list[int] = field(default_factory=lambda: [0]*100) # the nth index corresponds to the number of people who are n years old AND have the skills to work

    def working_age(self, minimum: int, maximum: int):
        num = 0
        for age in range(minimum, maximum + 1):
            num += self.ages[age]
        return num
    
    def total(self) -> int:
        t = 0
        for age in range(0, len(self.ages)):
            t += self.ages[age]

        return t



@dataclass
class SocietalResources(GameObject):
    population: Population = Population()
    employable_population: int = 0 # must be less than or equal to self.population.working_age
    morale: int = 50 

@dataclass
class EmpireResources(GameObject):
    corruption: int = 0
    knowledge: int = 0
