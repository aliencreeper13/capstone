from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional



from exceptions import AlreadyContainedException, BadAllegianceException, BadDirectionException
from gameobject import GameObject

from location import Path, PathDirection, GameNode
from unit import Unit
from constants import HALF_MORALE, MAX_MORALE
from utils import new_value_given_morale

import random

if TYPE_CHECKING:
    from empire import Empire
    from effects import Effect
    from job_requirements import JobRequirements

@dataclass
class ArmyAttributes(GameObject):
    hitpoints: int
    speed: int
    damage_per_tick: int
    morale: float = HALF_MORALE

class ArmyUnit(Unit):
    def __init__(self, name: str, size: int, effects: Effect, requirements: JobRequirements, base_attributes: ArmyAttributes, description: str=""):
        super().__init__(name=name,
                         size=size,
                         effects=effects,
                         requirements=requirements,
                         description=description
                         )

        self._allegiance: Optional[Empire] = None
        
        self._base_attributes: ArmyAttributes = base_attributes  # when morale = HALF_MORALE, the max attributes = the base attributes
        self._current_attributes: ArmyAttributes = base_attributes

        # all army units start 
        self._current_attributes.morale = HALF_MORALE

        self._morale_sensitivity = 0.01  # Default, can be tuned per unit

    def set_allegiance(self, empire: Empire):
        self._allegiance = empire

    @property
    def allegiance(self) -> Empire | None:
        return self._allegiance

    @property
    def current_attributes(self) -> ArmyAttributes:
        return self.current_attributes
    
    @property
    def current_morale(self) -> float:
        return self._current_attributes.morale
    
    # the max morale for an army unit
    @property
    def max_attributes(self) -> ArmyAttributes:
        return ArmyAttributes(
            hitpoints=new_value_given_morale(self._base_attributes.hitpoints, self.current_morale),
            speed=new_value_given_morale(self._base_attributes.speed, self.current_morale),
            damage_per_tick=new_value_given_morale(self._base_attributes.damage_per_tick, self.current_morale),
            morale=MAX_MORALE
        )
    
    def apply_damage(self, dmg: float):
        dmg = min(dmg, self._current_attributes.hitpoints)
        if dmg <= 0:
            return
        
        # Compute % of HP lost
        hp_before = self._current_attributes.hitpoints
        self._current_attributes.hitpoints -= dmg
        hp_lost_fraction = dmg / hp_before if hp_before > 0 else 0.0

        # Morale drops proportionally to HP lost
        morale_drop = hp_lost_fraction * MAX_MORALE * self._morale_sensitivity
        self._current_attributes.morale = max(0.0, self._current_attributes.morale - morale_drop)

    @property
    def is_dead(self) -> bool:
        return self._current_attributes.hitpoints <= 0
    
    
    
class Army(GameObject):
    def __init__(self, allegiance: Optional[Empire]):
        super().__init__()
        self._allegiance: Optional[Empire] = allegiance
        self._army_units: list[ArmyUnit] = []

        self._gamenode: Optional[GameNode] = None

        self._path: Optional[Path] = None
        self._path_position: Optional[float] = 0.0

    def in_gamenode(self) -> bool:
        return self._gamenode != None and isinstance(self._gamenode, GameNode)

    def on_path(self) -> bool:
        return self._path != None and isinstance(self._path, Path)

    # the army exits a gamenode (like a city) and embarks on a connected path
    def get_on_path(self, path: Path):
        if self.in_gamenode():
            self._gamenode.remove_army(self)
            path.add_army(army=self, from_node=self._gamenode)
            self._path = path
            self._gamenode = None

    # the army exits a path and enters into a gamenode (like a city)
    def get_on_gamenode(self, gamenode: GameNode):
        if self.on_path():  # this prevents the army from just teleporting. 
                            # This method is NOT used to deploy an army to a gamenode for the first time
            self._path.remove_army(self)
            gamenode.add_army(self)
            self._gamenode = gamenode
            self._path = None


    def move_along_path(self, path_direction: PathDirection):
        if self.on_path():
            if path_direction.FORWARDS:
                self._path.move_army(army=self, delta=+self.speed)
            elif path_direction.BACKWARDS:
                self._path.move_army(army=self, delta=-self.speed)
            else:
                raise BadDirectionException()
        

    def add_army_unit(self, army_unit: ArmyUnit):
        if army_unit.allegiance is not self._allegiance:
            raise BadAllegianceException()
        
        if army_unit in self._army_units:
            raise AlreadyContainedException()
        
        self._army_units.append(army_unit)
    
    @property
    def current_attributes(self) -> ArmyAttributes:
        if len(self._army_units) == 0:
            return ArmyAttributes(
            hitpoints=0,
            speed=0,
            damage_per_tick=0,
            morale=HALF_MORALE
        ) 
        total_hitpoints = 0
        total_damage_per_tick = 0
        total_morale = 0.0

        slowest_speed = float('inf')
        for army_unit in self._army_units:
            total_hitpoints += army_unit.current_attributes.hitpoints
            total_damage_per_tick + army_unit.current_attributes.damage_per_tick 
            total_morale + army_unit.current_attributes.morale

            if army_unit.current_attributes.speed < slowest_speed:
                slowest_speed = army_unit.current_attributes.speed

        average_morale = total_morale / len(self._army_units)

        assert 0 <= average_morale <= MAX_MORALE

        # the overall speed of the army is the speed of the slowest unit
        army_speed = slowest_speed

        return ArmyAttributes(
            hitpoints=total_hitpoints,
            speed=army_speed,
            damage_per_tick=total_hitpoints,
            morale=average_morale
        )
    
    @property
    def speed(self) -> int:
        return self.current_attributes.speed

    @property
    def current_tick(self) -> int:
        return self._allegiance.current_tick
    

    @property
    def size(self) -> int:
        total_size = 0
        for army_unit in self.army_units:
            total_size += army_unit.size
        return total_size
    
    def remove_dead_units(self):
        self._army_units = [u for u in self._army_units if not u.is_dead]

    @property
    def army_units(self) -> list[ArmyUnit]:
        return self._army_units

    @property
    def num_units(self) -> int:
        return len(self._army_units)
    
    @property
    def allegiance(self) -> Optional[Empire]:
        return self._allegiance
    
    def set_allegiance(self, empire: Empire):
        self._allegiance = empire
    
    def has_unit(self, army_unit: ArmyUnit):
        return army_unit in self._army_units
    
    
def battle_next_tick(army1: Army, army2: Army):
    """Run one tick of battle between two armies."""

    # Skip if either side is already dead
    if army1.num_units == 0 or army2.num_units == 0:
        return

    # Compute outgoing damage
    dmg1 = army1.current_attributes.damage_per_tick
    dmg2 = army2.current_attributes.damage_per_tick

    # Each side receives the other's damage
    _distribute_damage(army2, dmg1)  # army1 attacks army2
    _distribute_damage(army1, dmg2)  # army2 attacks army1

    # Remove dead units
    army1.remove_dead_units()
    army2.remove_dead_units()


def _distribute_damage(target_army: Army, total_damage: float):
    """Distribute damage across target army units based on morale bias."""
    if target_army.num_units == 0 or total_damage <= 0:
        return

    # The lower the morale, the higher the chance of being hit
    weights = []
    for army_unit in target_army.army_units:
        # Avoid division by zero; clamp morale to small epsilon
        weight = 1.0 / max(0.01, army_unit.current_morale)
        weights.append(weight)
    total_weight = sum(weights)
    if total_weight == 0:
        return

    # Apply proportionate damage
    for unit, weight in zip(target_army._army_units, weights):
        portion = weight / total_weight
        dmg = total_damage * portion
        unit.apply_damage(dmg)

        