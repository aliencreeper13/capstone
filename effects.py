from dataclasses import dataclass

# each of the effects are applied to the city each tick
@dataclass
class CityEffects:
    food_per_tick: int
    timber_per_tick: int
    wealth_per_tick: int
    metal_per_tick: int

# knowledge
@dataclass
class EmpireEffects:
    knowledge_per_tick: int