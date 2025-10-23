# I forgot what role this module is supposed to play lol

from typing import Optional, TYPE_CHECKING
from gameobject import GameObject

if TYPE_CHECKING:
    from city import City

class Block(GameObject):
    def __init__(self, x, y):
        self._x = x
        self._y = y

        self.city: Optional[City] = None  # 