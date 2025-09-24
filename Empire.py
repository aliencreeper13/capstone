from __future__ import annotations

from data import EmpireResources
from City import City
from game import Game, EmptyGame
from effects import Effects


class Empire:
    def __init__(self, autonomy: int):
        assert 0 <= autonomy <= 100
        self.empire_resources = EmpireResources()

        self.cities: list[City] = []
        self.capital: Empire = EmptyEmpire()

        self._knowledge: int = 50

        self._autonomy = autonomy

        self._game: Game = EmptyGame()

        

    def assigned_to_game(self) -> bool:
        return not self._game is EmptyGame()

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
        pass


class EmptyEmpire(Empire):
    """
    A city's allegiance to this empire means that the city has NO allegiance
    """
    # this makes this a singleton class
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(EmptyEmpire, cls).__new__(cls)
        return cls.instance