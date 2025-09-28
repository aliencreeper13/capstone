from dataclasses import dataclass
from math import ceil

@dataclass
class BuildingRequirements:
    _food_level1: int = 0
    _timber_level1: int = 0
    _wealth_level1: int = 0
    _metal_level1: int = 0
    _knowledge_level1: int = 0

    _exponent: float = 1.05

    def food(self, level: int) -> int:
        return ceil(self._food_level1 * self._exponent**(level - 1))
    
    def timber(self, level: int) -> int:
        return ceil(self._timber_level1 * self._exponent**(level - 1))
    
    def wealth(self, level: int) -> int:
        return ceil(self._wealth_level1 * self._exponent**(level - 1))
    
    def metal(self, level: int) -> int:
        return ceil(self._metal_level1 * self._exponent**(level - 1))
    
    def knowledge(self, level: int) -> int:
        return ceil(self._knowledge_level1 * self._exponent**(level - 1))
