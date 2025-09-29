from effects import Effects

from job_requirements import JobRequirements

class Unit:
    def __init__(self,  name: str, size: int = 1, effects: Effects = Effects):
        self.name = name
        self._size = size
        self._level = 1
        self._effects: Effects = effects

        

    @property
    def size(self) -> int:
        return self._size
    
    @property
    def effects(self) -> Effects:
        return self._effects
    
    @property
    def level(self) -> int:
        return self._level
    
    
    
    def upgrade(self):
        # todo: upgrade effects as well (soon to be implemented)
        self._level += 1
    
