from __future__ import annotations

from City import City, EmptyCity

from unit import Unit

class Building(Unit):
    def __init__(self):
        self._city: City = EmptyCity() # indicates what city it is part of

    def set_city(self, city: City):
        pass