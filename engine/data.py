from __future__ import annotations

from dataclasses import dataclass, field

from gameobject import GameObject

# this is probably overkill but whatever (I got chatgpt to do this for me)
class GameDataclass(GameObject):
    def __operate(self, other, op):
        """Helper to perform numeric operation `op` on numeric attributes."""
        new_obj = self.__class__()
        
        for attr, value in self.__dict__.items():
            if isinstance(value, (int, float)):
                if isinstance(other, self.__class__):
                    other_value = getattr(other, attr, 0)
                    if isinstance(other_value, (int, float)):
                        setattr(new_obj, attr, op(value, other_value))
                    else:
                        setattr(new_obj, attr, value)
                elif isinstance(other, (int, float)):
                    setattr(new_obj, attr, op(value, other))
                else:
                    raise TypeError(
                        f"Unsupported operand type(s) for operation: "
                        f"'{type(self).__name__}' and '{type(other).__name__}'"
                    )
            else:
                setattr(new_obj, attr, value)
        return new_obj

    def __add__(self, other):
        return self.__operate(other, lambda a, b: a + b)

    def __sub__(self, other):
        return self.__operate(other, lambda a, b: a - b)

    def __mul__(self, other):
        return self.__operate(other, lambda a, b: a * b)

    def __truediv__(self, other):
        return self.__operate(other, lambda a, b: a / b if b != 0 else float('inf'))

    def __neg__(self):
        new_obj = self.__class__()
        for attr, value in self.__dict__.items():
            if isinstance(value, (int, float)):
                setattr(new_obj, attr, -value)
            else:
                setattr(new_obj, attr, value)
        return new_obj
    

@dataclass
class ExpendableCityResources(GameDataclass):
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
    employable_population: int = 0 # must be less than or equal to self.population.working_age. Decreases when people work
    employed_population: int = 0
    morale: int = 50 

@dataclass
class ExpendableEmpireResources(GameDataclass):
    corruption: int = 0
    knowledge: int = 0


if __name__ == "__main__":
    original = ExpendableCityResources(
        food=45
    )
    increases = ExpendableCityResources(
        food=45
    )
    print(original + increases)