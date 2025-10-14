from dataclasses import dataclass

from data import ExpendableCityResources

from typing import TYPE_CHECKING, Optional

from gameobject import GameObject

if TYPE_CHECKING:
    from city import City
    from unit import Unit

# each of the effects are applied to the city each tick
@dataclass
class Effect(GameObject):
    duration_in_ticks: int = 0  # if duration is 0, then it's indefinite

    material_resources_per_tick: ExpendableCityResources = ExpendableCityResources.empty_resources()
    morale_per_tick: float = 0.0
    knowledge_per_tick: int = 0

    defense_offered: int = 0

    new_people_per_tick: int = 0  # how many new people are born
    dead_people_per_tick: int = 0 # how many people die per tick

    capital_effect: bool = False  # only applies when the city in question is the capital
    contingent_on: list[Unit] # effect only active if unit is active, or if set to None

    @classmethod
    def empty_effects(cls):
        return cls(duration_in_ticks=0,
                       material_resources_per_tick=ExpendableCityResources.empty_resources(),
                       knowledge_per_tick=0)
    
    def is_indefinite(self) -> bool:
        return self.duration_in_ticks == 0
    
    def is_universal(self) -> bool:
        return False
    
    def is_active(self) -> bool:
        for unit_ in self.contingent_on:
            if not unit_.is_active():
                return False
            
        return True

class UniversalEffect(Effect):
    def is_universal(self) -> bool:
        return True

@dataclass
class EffectWithTicksleft:
    effect: Effect
    ticks_left: int

    def progress(self):
        self.ticks_left -= 1
        if self.ticks_left <= 0:
            self.ticks_left = 0

    def is_finished(self) -> bool:
        # a duration of 0 ticks indicates indefinite duration
        if self.effect.is_indefinite():
            return False
        return self.ticks_left <= 0
    
    
    
    

    
        
