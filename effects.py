from dataclasses import dataclass

from data import CityResources

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from city import City

# each of the effects are applied to the city each tick
@dataclass
class Effects:
    duration_in_ticks: int = 0

    material_resources_per_tick: CityResources = CityResources.empty_resources()
    morale_per_tick: float = 0.0
    knowledge_per_tick: int = 0

    @classmethod
    def empty_effects(cls):
        return Effects(duration_in_ticks=0,
                       material_resources_per_tick=CityResources.empty_resources(),
                       knowledge_per_tick=0)
    
    def is_indefinite(self) -> bool:
        return self.duration_in_ticks == 0
    
@dataclass
class EffectWithTicksleft:
    effects: Effects
    ticks_left: int

    def progress(self):
        self.ticks_left -= 1
        if self.ticks_left <= 0:
            self.ticks_left = 0

    def is_finished(self) -> bool:
        # a duration of 0 ticks indicates indefinite duration
        if self.effects.is_indefinite():
            return False
        return self.ticks_left <= 0
    
    

    
        
