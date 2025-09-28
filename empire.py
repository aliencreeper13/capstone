from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from constants import HALF_AUTONOMY
from data import EmpireResources

from game import Game, EmptyGame
# from effects import Effects


if TYPE_CHECKING:
    from city import City

class Empire:
    def __init__(self, autonomy: int):
        assert 0 <= autonomy <= 100
        self.empire_resources = EmpireResources()

        self.cities: list[City] = []
        self.capital: Optional[Empire] = None

        self._knowledge: int = 50

        self._autonomy = autonomy

        self._game: Optional[Game] = None

        

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
        self.cities.append(city)

    def remove_city(self, city: City):
        city.declare_independence()
        self.cities.remove(city)

    def set_city_as_capital(self, city: City):
        if city.allegiance is self:
            self.capital.remove_as_capital() # current capital

            self.capital = city # set as new capital
            self.capital.set_city_as_capital()

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
        for city in self.cities:
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