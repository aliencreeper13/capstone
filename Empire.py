from __future__ import annotations

from data import EmpireResources
from City import City


class Empire:
    def __init__(self, autonomy: int):
        assert 0 <= autonomy <= 100
        self.empire_resources = EmpireResources()

        self.cities: list[City] = []
        self.capital: Empire = EmptyEmpire()

        self._knowledge: int = 50

        self._autonomy = autonomy

        

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


class EmptyEmpire(Empire):
    """
    A city's allegiance to this empire means that the city has NO allegiance
    """
    # this makes this a singleton class
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(EmptyEmpire, cls).__new__(cls)
        return cls.instance