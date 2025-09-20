from __future__ import annotations # avoid circular import error

from Empire import Empire, EmptyEmpire
from data import MaterialResources, Population, SocietalResources
from building import Building
from typing import Optional
from queue import Queue

from job import Job

class City:
    def __init__(self, capital=False, size: int = 5, morale: int = 50):
        self.resources: MaterialResources = MaterialResources()
        self.societal_resources: SocietalResources = SocietalResources()
        self.defense = 100
        self.capital = capital
        self._allegiance: Empire = EmptyEmpire() # start off with no allegiance
        self._size = size
        self._morale = morale

        self._buildings: list[Building] = []
        self._running_jobs: Queue[Job] = Queue() # represents all running jobs (construction, etc.)

    # this runs every tick
    def mainloop():
        pass

    @property
    def allegiance(self):
        return self._allegiance
    
    # the autonomy of a city is the autonomy permitted by the empire
    @property
    def autonomy(self):
        return self.allegiance.autonomy
    
    @property
    def knowledge(self):
        return self.allegiance.knowledge

    
    def set_allegiance(self, allegiance: Empire):
        self._allegiance = allegiance

    def declare_independence(self):
        self._allegiance = EmptyEmpire()

    def remove_as_capital(self):
        self.capital = False

    def set_as_capital(self):
        self.capital = True

    def _remaining_space(self) -> int:
        total_occupied_space: int = 0
        for building in self._buildings:
            total_occupied_space += building.size

        return self._size - total_occupied_space


    # private function
    def _add_building(self, building: Building):
        assert self._remaining_space() > 0
        self._buildings.append(building)
        

    @property
    def morale(self) -> int:
        return self._morale

    @morale.setter
    def morale(self, new_morale: int):
        assert 0 <= new_morale <= 100
        self._morale = new_morale

class EmptyCity(City):
    """
    A unit's allegiance to this city means that the unit has NO allegiance
    """
    # this makes this a singleton class
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(EmptyCity, cls).__new__(cls)
        return cls.instance