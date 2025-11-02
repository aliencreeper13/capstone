"""
Gameplay package: Game engine and mechanics.

This package contains the main game loop, event system, and spatial/location systems.

Modules:
    - game: Main game loop and tick management
    - location: World map and location data structures
    - events: Game event system for tracking state transitions
"""

# Re-export main gameplay classes for convenient imports
from .location import GameNode, Path, PathDirection, WorldMap
from .game import Game, EmptyGame
from .events import GameEvent, EventType

__all__ = [
    "GameNode",
    "Path",
    "PathDirection",
    "WorldMap",
    "Game",
    "EmptyGame",
    "GameEvent",
    "EventType",
]