from __future__ import annotations
from typing import Optional
from effects import Effect

from job_requirements import JobRequirements

class Unit:
    def __init__(self,  name: str, size: int = 1, effects: Effect = Effect):
        self.name = name
        self._size = size
        self._level = 1
        self._effects: Effect = effects
        self._active = False

    def set_active(self):
        self._active = True

    def set_inactive(self):
        self._active = False


    def is_active(self):
        return self._active

    @property
    def size(self) -> int:
        return self._size
    
    @property
    def effects(self) -> Effect:
        return self._effects
    
    @property
    def level(self) -> int:
        return self._level
    
    
    
    def upgrade(self):
        # todo: upgrade effects as well (soon to be implemented)
        self._level += 1
    
