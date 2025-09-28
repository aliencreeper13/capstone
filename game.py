from __future__ import annotations

from typing import TYPE_CHECKING
from time import sleep
if TYPE_CHECKING:
    from empire import Empire

class Game:
    def __init__(self, empires: list[Empire] = []):
        self._current_tick: int = 0
        self._empires: list[Empire] = empires
        for empire in self._empires:
            assert not empire.assigned_to_game()
            empire.assign_to_game(self)
        self.seconds_per_tick = 1
        self._begun: bool = False

    def mainloop(self):
        self.next_tick()
            
    def begin_game(self):
        self._begun = True
        while True:
            self.next_tick()
            sleep(self.seconds_per_tick)
            print("current tick", self.current_tick)

    def add_empire(self, empire: Empire):
        # assert not self._begun # uncomment this if you want to prevent empires from being added mid-game
        assert not empire.assigned_to_game()
        empire.assign_to_game(self)
        self._empires.append(empire)

    def next_tick(self):
        self._current_tick += 1
        for empire in self._empires:
            print("Updating empire", empire)
            empire.update(self._current_tick)

    @property
    def current_tick(self) -> int:
        return self._current_tick

class EmptyGame(Game):
    """
    A game part of `EmptyGame` means it hasn't been assigned to an empty game yet
    """
    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super().__new__(cls)
            # Call Game.__init__ *only once*, right after creating the instance
            Game.__init__(cls.instance, empires=[])
        return cls.instance
    
    def __init__(self):
        # Override __init__ so Empire.__init__ is NOT called again
        pass