from dataclasses import dataclass
from City import City
from data import MaterialResources

# each of the effects are applied to the city each tick
@dataclass
class Effects:
    duration_in_ticks: int = 0

    material_resources_per_tick: MaterialResources = MaterialResources.empty_resources()
    morale_per_tick: float 
    knowledge_per_tick: int

    @classmethod
    def empty_effects(cls):
        return Effects(duration_in_ticks=0,
                       material_resources_per_tick=MaterialResources.empty_resources(),
                       knowledge_per_tick=0)
    
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
        if self.effects.duration_in_ticks == 0:
            return False
        return self.ticks_left <= 0
    
    

    
        
