"""
Game engine: Main game loop and empire/tick management.

The Game engine coordinates:
- Multiple empires playing simultaneously
- Game tick progression (each tick represents time passing)
- World map and spatial organization
- Game state and lifecycle (not started, running, finished)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from time import sleep

from ..core.gameobject import GameObject, public_client_property
from .location import GameNode

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
        Settlement checks are performed to establish new cities on unclaimed nodes
        when 10+ settlers are present.
        """
        self._current_tick += 1
        for empire in self._empires:
            empire.update(self._current_tick)
        
        # Check for settler settlements on unclaimed nodes
        self._check_settler_settlements()

    @public_client_property
    def current_tick(self) -> int:
        """Get the current game tick."""
        return self._current_tick
    
    @property
    def worldmap(self) -> WorldMap:
        """Get the world map."""
        return self._worldmap

    def _check_settler_settlements(self) -> None:
        """
        Check all unclaimed nodes for settlement conditions.
        
        If an unclaimed node has 10 or more Settlers from the same empire,
        convert it to a City belonging to that empire.
        """
        if self._worldmap is None:
            return
        
        # Get a copy of nodes list since we'll modify it during iteration
        nodes_to_check = list(self._worldmap.get_nodes())
        
        for node in nodes_to_check:
            # Skip if node is already claimed
            if node.is_claimed:
                continue
            
            # Count settlers and group them by empire
            settler_groups: dict[Empire, int] = {}
            for group in node.armies():
                for unit in group.mobile_units:
                    # Check if unit is a Settler
                    if type(unit).__name__ == "Settler":
                        empire = unit.allegiance
                        if empire not in settler_groups:
                            settler_groups[empire] = 0
                        settler_groups[empire] += 1
            
            # Check if any empire has 10+ settlers on this node
            for empire, settler_count in settler_groups.items():
                if settler_count >= 10 and empire is not None:
                    self._settle_node_as_city(node, empire)
                    break  # Only one empire can settle per node per tick

    def _settle_node_as_city(self, node: GameNode, empire: Empire) -> None:
        """
        Establish a City on an unclaimed GameNode.
        
        The new city is added to the node
        
        Args:
            node: The GameNode to settle
            empire: The empire establishing the city
        """
        from ..entities.city import City
        
        # Create a new city within the node
        new_city = City(gamenode=node, size=5)
        new_city.set_allegiance(empire)
        
        # Add the city to the node
        node.set_city(new_city)
        
        # Add the city to the empire
        empire.add_city(new_city)
        
        # Mark the node as claimed
        node.claim_for_empire(empire)

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