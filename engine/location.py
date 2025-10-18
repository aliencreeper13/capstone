from __future__ import annotations

from enum import Enum
from math import sqrt
from typing import TYPE_CHECKING

from exceptions import BadGameNodeException
from gameobject import GameObject
if TYPE_CHECKING:
    from army import ArmyUnit, Army


class PathDirection(Enum):
    FORWARDS =  +1
    BACKWARDS = -1

# todo: generate 
class WorldMap(GameObject):
    def __init__(self, size=tuple[int, int]):
        super().__init__()
        self._size: tuple[int, int] = size

        self._nodes: list[GameNode] = []
        self._paths: dict[tuple[GameNode, GameNode], Path] = {}


class Path(GameObject):
    def __init__(self, game_node1: GameNode, game_node2: GameNode):
        self._game_node1: GameNode = game_node1
        self._game_node2: GameNode = game_node2

        self._distance = GameNode.distance(self._game_node1, self._game_node2)

        self._armies_and_coords: dict[Army, int] = {}  # armies and their corresponding position on the path

    @property
    def distance(self) -> float | int:
        return self._distance
    
    @property
    def min_position(self) -> float: # yeah I know this seems unnecessary, but you never know...
        return 0.0
    
    @property
    def max_position(self) -> float:
        return self.distance - 1
    
    def move_army(self, army: Army, delta: float):
        if army in self._armies_and_coords.keys():
            self._armies_and_coords[army] += delta

            # if army goes below minimum position, then it effectively has moved into the first gamenode
            if self._armies_and_coords[army] < self.min_position:
                # self.remove_army(army)
                # self._game_node1.add_army(army)
                army.get_on_gamenode(self._game_node1)

            elif self._armies_and_coords[army] > self.max_position:
                # self.remove_army(army)
                # self._game_node2.add_army(army)
                army.get_on_gamenode(self._game_node2)

    # when adding unit to path, the unit must come from one of the nodes
    def add_army(self, army: Army, from_node: GameNode):
        if not (from_node is self._game_node1 or from_node is self._game_node2):
            raise BadGameNodeException()
        
        if from_node is self._game_node1:
            self._armies_and_coords.update({army: self.min_position})
        elif from_node is self._game_node2:
            self._armies_and_coords.update({army: self.max_position})

    def remove_army(self, army: Army):
        del self._armies_and_coords[army]

class GameNode(GameObject):
    def __init__(self, coords: tuple[int, int], size: int):
        self._x: int = coords[0]
        self._y: int = coords[1]
        
        self._size: int = size
        self._armies: list[Army] = []

    def add_army(self, army: Army):
        self._armies.append(army)
        

    def remove_army(self, army: Army):
        self._armies.remove(army)

    @property
    def x(self) -> int:
        return self._x
    
    @property
    def y(self) -> int:
        return self._y
    
    @staticmethod  # technically, this doesn't need to be static. 
                     #However, I feel like it's good to put it in this class for organizational purposes
    def distance(game_node1: GameNode, game_node2: GameNode) -> float:
        x1 = game_node1.x
        y1 = game_node1.y

        x2 = game_node2.x
        y2 = game_node2.y
        return sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    

