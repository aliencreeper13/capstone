from dataclasses import dataclass

@dataclass
class MaterialResources:
    food: int = 0
    timber: int = 0
    wealth: int = 0
    metal: int = 0

    @classmethod
    def empty_resources(cls):
        return MaterialResources(
            food=0,
            timber=0,
            wealth=0,
            metal=0
        )
@dataclass
class Population:
    ages: list[int] = [0]*100 # the nth index corresponds to the number of people who are n years old
    ages_can_work: list[int] = [0]*100 # the nth index corresponds to the number of people who are n years old AND have the skills to work

    def working_age(self, minimum: int, maximum: int):
        num = 0
        for age in range(minimum, maximum + 1):
            num += self.ages[age]
        return num


@dataclass
class SocietalResources:
    population: Population = Population()
    employable_population: int = 0 # must be less than or equal to self.population.working_age
    morale: int = 50 

@dataclass
class EmpireResources:
    corruption: int = 0
    knowledge: int = 0
