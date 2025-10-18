from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from constants import HALF_AUTONOMY
from data import ExpendableEmpireResources

from effects import EffectWithTicksleft, Effect, UniversalEffect
from exceptions import BadEffect, CapitalExclusiveException
from game import Game, EmptyGame
from gameobject import GameObject
from ideology import Ideology
# from effects import Effects


if TYPE_CHECKING:
    from city import City

class Empire(GameObject):
    def __init__(self, autonomy: int, capital_city: City, ideology: Ideology):
        assert 0 <= autonomy <= 100
        self._empire_resources = ExpendableEmpireResources()

        
        self._capital: City = capital_city

        self._cities: list[City] = [self._capital]

        self._knowledge: int = 50

        self._autonomy = autonomy

        self._game: Optional[Game] = None

        self._empire_effects_with_ticks_left: list[EffectWithTicksleft] = []
        self._ideology: Ideology = ideology
        for ideological_effect in ideology.effects:
            self.add_universal_or_capital_effect(ideological_effect)

    @property
    def capital(self) -> City:
        return self._capital
    
    def add_universal_or_capital_effect(self, effect: Effect):
        if not( effect.is_universal() or effect.capital_effect):
            raise BadEffect()
        
        # add universal effect to empire list, to keep reference of all universal effects
        self._empire_effects_with_ticks_left.append(EffectWithTicksleft(
            effect=effect,
            ticks_left=effect.duration_in_ticks
        ))

        # each city gets access to this effect
        # yes, even the non-universal capital effect
        # it's just that the city won't run this effect
        # unless it becomes the capital
        for city in self._cities:
            city.add_effect(effect)


    def assigned_to_game(self) -> bool:
        return not self._game is None

    def assign_to_game(self, game: Game):
        if not self.assigned_to_game():  # only assign to a game if it is currently not assigned
            self._game = game

    @property
    def game(self):
        return self._game

    def add_city(self, city: City):
        city.set_allegiance(self) # set city's allegiance to empire
        self._cities.append(city)

    def remove_city(self, city: City):
        city.declare_independence()
        self._cities.remove(city)

    def set_city_as_capital(self, city: City):
        if city.allegiance is self:
            self._capital.remove_as_capital() # current capital

            self._capital = city # set as new capital
            self._capital.set_city_as_capital()

    @property
    def knowledge(self) -> int: 
        return self._knowledge
    
    @property
    def autonomy(self) -> int:
        return self._autonomy
    
    @property
    def current_tick(self):
        return self._game.current_tick
    
    # updates all data to next tick
    def update(self, current_tick: int):
        for city in self._cities:
            print("updating city", city)
            city.update()


class EmptyEmpire(Empire):
    """
    A city's allegiance to this empire means that the city has NO allegiance
    """
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super().__new__(cls)
            # Call Empire.__init__ *only once*, right after creating the instance
            Empire.__init__(cls.instance, autonomy=0)
        return cls.instance
    
    def __init__(self):
        # Override __init__ so Empire.__init__ is NOT called again
        pass