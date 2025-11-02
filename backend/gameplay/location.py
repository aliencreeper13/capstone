"""
Location and path management for the game world.

This module defines the spatial structure of the game world:
- GameNode: A location on the map (city location or strategic point)
- Path: A connection between two GameNodes for army movement
- PathDirection: Directional enum for path traversal
- WorldMap: The overall map structure (placeholder for future expansion)

Armies move along paths between game nodes, with their position tracked as a
floating-point value between 0 (at starting node) and distance (at ending node).
"""

from __future__ import annotations

from enum import Enum
from math import sqrt
from typing import TYPE_CHECKING

from ..core.exceptions import BadGameNodeException
from ..core.gameobject import GameObject

if TYPE_CHECKING:
    from ..entities.army import Army, Troop


class PathDirection(Enum):
    """Direction of movement along a path."""
    FORWARDS = +1
    BACKWARDS = -1


class WorldMap(GameObject):
    """
    Represents the overall game map structure.
    
    Currently a placeholder for future expansion. Will eventually manage:
    - All game nodes on the map
    - All paths between nodes
    - Map size and terrain
    """
    
    def __init__(self, size: tuple[int, int]):
        """
        Initialize a new world map.
        
        Args:
            size: (width, height) of the map in units
        """
        super().__init__()
        self._size: tuple[int, int] = size
        self._nodes: list[GameNode] = []
        self._paths: dict[tuple[GameNode, GameNode], Path] = {}


class Path(GameObject):
    """
    Represents a connection between two GameNodes.
    
    Armies move along paths with their position tracked as a float from 0 to distance.
    When position goes below 0 or above distance, the army moves to the connected node.
    """
    
    def __init__(self, game_node1: GameNode, game_node2: GameNode):
        """
        Create a path connecting two game nodes.
        
        Args:
            game_node1: First node (starting node)
            game_node2: Second node (ending node)
        """
        super().__init__()
        self._game_node1: GameNode = game_node1
        self._game_node2: GameNode = game_node2
        self._distance = GameNode.distance(self._game_node1, self._game_node2)
        
        # Armies on this path and their position (0 to distance)
        self._armies_and_coords: dict[Army, float] = {}

    @property
    def distance(self) -> float | int:
        """The length of this path between the two nodes."""
        return self._distance
    
    @property
    def min_position(self) -> float:
        """Minimum position on the path (at starting node)."""
        return 0.0
    
    @property
    def max_position(self) -> float:
        """Maximum position on the path (at ending node)."""
        return self.distance - 1
    
    def move_army(self, army: Army, delta: float) -> None:
        """
        Move an army along this path by a given distance.
        
        If the army's position goes below min_position or above max_position,
        the army is automatically moved to the connected node.
        
        Args:
            army: The army to move
            delta: The distance to move (can be negative)
        """
        if army in self._armies_and_coords.keys():
            self._armies_and_coords[army] += delta

            # If army goes below minimum position, move to first node
            if self._armies_and_coords[army] < self.min_position:
                army.get_on_gamenode(self._game_node1)

            # If army goes above maximum position, move to second node
            elif self._armies_and_coords[army] > self.max_position:
                army.get_on_gamenode(self._game_node2)

    def add_army(self, army: Army, from_node: GameNode) -> None:
        """
        Add an army to this path from one of its connected nodes.
        
        Args:
            army: The army to add to the path
            from_node: The node the army is coming from (must be one of the path's nodes)
            
        Raises:
            BadGameNodeException: If from_node is not one of this path's nodes
        """
        if not (from_node is self._game_node1 or from_node is self._game_node2):
            raise BadGameNodeException(
                f"Army must originate from one of the path's connected nodes. "
                f"Got node at ({from_node.x}, {from_node.y}) but path connects "
                f"({self._game_node1.x}, {self._game_node1.y}) to "
                f"({self._game_node2.x}, {self._game_node2.y})"
            )
        
        # Place army at the starting position on the path
        if from_node is self._game_node1:
            self._armies_and_coords.update({army: self.min_position})
        elif from_node is self._game_node2:
            self._armies_and_coords.update({army: self.max_position})

    def remove_army(self, army: Army) -> None:
        """
        Remove an army from this path.
        
        Args:
            army: The army to remove
        """
        del self._armies_and_coords[army]


class GameNode(GameObject):
    """
    Represents a location on the game map where armies can be stationed.
    
    Each node has:
    - Coordinates (x, y)
    - A size (perhaps for future expansion purposes)
    - A list of armies currently stationed there
    """
    
    def __init__(self, coords: tuple[int, int], size: int):
        """
        Create a new game node at the given coordinates.
        
        Args:
            coords: (x, y) coordinates of this node
            size: The size/capacity of this node
        """
        super().__init__()
        self._x: int = coords[0]
        self._y: int = coords[1]
        self._size: int = size
        self._armies: list[Army] = []

    def add_army(self, army: Army) -> None:
        """
        Station an army at this node.
        
        Args:
            army: The army to station here
        """
        self._armies.append(army)
    
    def armies(self) -> list[Army]:
        """Get all armies currently stationed at this node."""
        return self._armies

    def remove_army(self, army: Army) -> None:
        """
        Remove an army from this node.
        
        Args:
            army: The army to remove
        """
        self._armies.remove(army)

    @property
    def x(self) -> int:
        """X coordinate of this node."""
        return self._x
    
    @property
    def y(self) -> int:
        """Y coordinate of this node."""
        return self._y
    
    @property
    def coords(self) -> tuple[int, int]:
        """Coordinates of this node as (x, y) tuple."""
        return (self._x, self._y)
    
    @property
    def size(self) -> int:
        """Size/capacity of this node."""
        return self._size
    
    @staticmethod
    def distance(game_node1: GameNode, game_node2: GameNode) -> float:
        """
        Calculate the Euclidean distance between two game nodes.
        
        Args:
            game_node1: First node
            game_node2: Second node
            
        Returns:
            The distance between the two nodes
        """
        x1 = game_node1.x
        y1 = game_node1.y
        x2 = game_node2.x
        y2 = game_node2.y
        return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)