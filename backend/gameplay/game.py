"""
Game engine: Main game loop and empire/tick management.

The Game engine coordinates:
- Multiple empires playing simultaneously
- Game tick progression (each tick represents time passing)
- World map and spatial organization
- Game state and lifecycle (not started, running, finished)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from time import sleep

from ..core.gameobject import GameObject

if TYPE_CHECKING:
    from ..entities.empire import Empire
    from .location import WorldMap


class Game(GameObject):
    """
    The main game engine that coordinates all game systems.
    
    Manages:
    - Multiple empires playing simultaneously
    - Game tick progression
    - World map/spatial structure
    - Game lifecycle (begin, running, stop)
    
    Each tick advances all empires' internal state (city updates, job
    progression, resource production, etc.).
    """
    
    def __init__(self, worldmap: WorldMap, empires: list[Empire] | None = None):
        """
        Initialize a new game.
        
        Args:
            worldmap: The world map for this game
            empires: Initial list of empires (default: empty list)
        """
        super().__init__()
        
        if empires is None:
            empires = []
        
        self._current_tick: int = 0
        self._empires: list[Empire] = empires
        
        # Assign all empires to this game
        for empire in self._empires:
            assert not empire.assigned_to_game(), "Empire already assigned to another game"
            empire.assign_to_game(self)
        
        # Timing configuration
        self.seconds_per_tick = 1
        
        # Game state
        self._begun: bool = False
        self._worldmap: WorldMap = worldmap

    # ========== Tick Management ==========

    def next_tick(self) -> None:
        """
        Advance the game by one tick.
        
        All empires and their cities process their actions, resources
        are produced/consumed, jobs progress, etc.
        """
        self._current_tick += 1
        for empire in self._empires:
            empire.update(self._current_tick)

    @property
    def current_tick(self) -> int:
        """Get the current game tick."""
        return self._current_tick

    # ========== Game Lifecycle ==========

    def mainloop(self) -> None:
        """
        Execute a single game tick (used for manual testing/stepping).
        """
        self.next_tick()

    def begin_game(self) -> None:
        """
        Start the main game loop.
        
        Continuously advances ticks with a delay between them,
        printing tick progress. Runs until stopped externally.
        """
        self._begun = True
        while True:
            self.next_tick()
            sleep(self.seconds_per_tick)
            print("current tick", self.current_tick)

    # ========== Empire Management ==========

    def add_empire(self, empire: Empire) -> None:
        """
        Add an empire to the game.
        
        The empire can be added before the game starts or mid-game
        (though mid-game addition may have balancing implications).
        
        Args:
            empire: The empire to add
        """
        assert not empire.assigned_to_game(), "Empire already assigned to a game"
        empire.assign_to_game(self)
        self._empires.append(empire)


class EmptyGame(Game):
    """
    Singleton representing a game with no empire assignment.
    
    Similar to EmptyEmpire, this is used to represent "no game" state.
    An empire's game reference to EmptyGame means it hasn't been assigned
    to an actual game yet.
    
    Note: Using None is actually simpler. This class is kept for reference.
    """
    
    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if not hasattr(cls, "instance"):
            cls.instance = super().__new__(cls)
            
            # Initialize with empty worldmap reference and no empires
            # (only called once on first instantiation)
            Game.__init__(cls.instance, worldmap=None, empires=[])
        return cls.instance
    
    def __init__(self):
        """
        Override __init__ to prevent re-initialization.
        
        Since this is a singleton, we don't want __init__ called multiple times.
        """
        pass