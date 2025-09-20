from dataclasses import dataclass

@dataclass
class UnitRequirements:
    level: int  # if level=1, then this refers to the requirements to create it for the first time
    food: int
    timber: int
    wealth: int
    metal: int
    knowledge: int
