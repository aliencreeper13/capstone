"""
Army system for military units and combat mechanics.

Armies are composed of troops and can move across the map, attack cities,
and engage in combat with other armies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional
import random

from ..core.constants import HALF_MORALE, MAX_MORALE
from ..core.gameobject import GameObject
from ..core.engine_utils import soft_isinstance
from ..systems.game_utils import new_value_given_morale
from ..gameplay.location import Path, PathDirection, GameNode
from .unit import Unit
from ..core.exceptions import (
    AlreadyContainedException,
    BadAllegianceException,
    BadDirectionException,
    IllegalMoveException
)

if TYPE_CHECKING:
    from .empire import Empire
    from ..systems.effects import Effect
    from ..systems.job_requirements import JobRequirements
    from .city import City


@dataclass
class ArmyAttributes(GameObject):
    """
    Represents the combat attributes of an army or troop.
    
    Attributes:
        hitpoints: Current HP (when 0 or below, unit is destroyed)
        speed: Movement speed along paths
        damage_per_tick: Damage dealt per combat tick
        morale: Combat morale affecting combat effectiveness (0-100)
    """
    hitpoints: float
    speed: float
    damage_per_tick: float
    morale: float = HALF_MORALE


class Troop(Unit):
    """
    A military unit that can be added to armies.
    
    Troops have combat attributes, morale, and damage mechanics.
    Morale affects combat effectiveness - lower morale = reduced stats and higher casualty rates.
    
    Class attributes:
        base_attributes: Base combat stats (overridden by subclasses)
    
    Instance attributes:
        _allegiance: Empire this troop belongs to
        _base_attributes: Stats at neutral morale
        _current_attributes: Current stats adjusted by morale
        _morale_sensitivity: How much morale affects combat effectiveness
    """
    
    base_attributes: ArmyAttributes
    
    def __init__(self, *args, **kwargs):
        """Initialize troop with base combat attributes and neutral morale."""
        super().__init__(*args, **kwargs)
        self._allegiance: Optional[Empire] = None
        
        self._base_attributes: ArmyAttributes = self.base_attributes
        self._current_attributes: ArmyAttributes = self.base_attributes
        self._current_attributes.morale = HALF_MORALE
        self._morale_sensitivity = 0.01

    def set_allegiance(self, empire: Empire):
        """Set the empire this troop serves."""
        self._allegiance = empire

    @property
    def allegiance(self) -> Optional[Empire]:
        """Get the empire this troop is allegiant to."""
        return self._allegiance

    @property
    def current_attributes(self) -> ArmyAttributes:
        """Get current combat attributes (adjusted for morale)."""
        return self._current_attributes
    
    @property
    def current_morale(self) -> float:
        """Get current morale level."""
        return self._current_attributes.morale
    
    @property
    def max_attributes(self) -> ArmyAttributes:
        """
        Get maximum possible attributes at max morale.
        
        Returns stats scaled up to reflect max morale condition.
        """
        return ArmyAttributes(
            hitpoints=new_value_given_morale(self._base_attributes.hitpoints, MAX_MORALE),
            speed=new_value_given_morale(self._base_attributes.speed, MAX_MORALE),
            damage_per_tick=new_value_given_morale(self._base_attributes.damage_per_tick, MAX_MORALE),
            morale=MAX_MORALE
        )
    
    def apply_damage(self, dmg: float):
        """
        Apply damage to this troop.
        
        Damage reduces HP and causes morale drop proportional to HP lost.
        Units with low morale take higher casualties (morale-based targeting).
        
        Args:
            dmg: Damage to apply (clamped to current HP)
        """
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
        """Return True if troop is dead (HP <= 0)."""
        return self._current_attributes.hitpoints <= 0


class Army(GameObject):
    """
    A military force composed of multiple troops.
    
    Armies have combined attributes, can move on paths, occupy game nodes (cities),
    and engage in combat. Army speed is limited by slowest unit.
    
    Instance attributes:
        _allegiance: Empire this army serves
        _army_units: List of troops in this army
        _gamenode: City or location this army is currently in
        _path: Path this army is currently traveling on
        _path_position: Position along current path (0.0-1.0)
    """
    
    def __init__(self, allegiance: Optional[Empire]):
        """Initialize empty army for an empire."""
        super().__init__()
        self._allegiance: Optional[Empire] = allegiance
        self._army_units: list[Troop] = []
        self._gamenode: Optional[GameNode] = None
        self._path: Optional[Path] = None
        self._path_position: Optional[float] = 0.0

    def in_gamenode(self) -> bool:
        """Return True if army is currently in a game node (city)."""
        return self._gamenode is not None and isinstance(self._gamenode, GameNode)

    def on_path(self) -> bool:
        """Return True if army is currently traveling on a path."""
        return self._path is not None and isinstance(self._path, Path)

    def get_on_path(self, path: Path):
        """Move army from current game node onto a path."""
        if self.in_gamenode():
            self._gamenode.remove_army(self)
            path.add_army(army=self, from_node=self._gamenode)
            self._path = path
            self._gamenode = None

    def get_on_gamenode(self, gamenode: GameNode):
        """Move army from current path into a game node."""
        if self.on_path():
            self._path.remove_army(self)
            gamenode.add_army(self)
            self._gamenode = gamenode
            self._path = None

    def move_along_path(self, path_direction: PathDirection):
        """
        Move army along path in given direction.
        
        Args:
            path_direction: Direction to move (FORWARDS or BACKWARDS)
            
        Raises:
            BadDirectionException: If direction is invalid
            IllegalMoveException: If army is not on a path
        """
        if self.on_path():
            if path_direction.FORWARDS:
                self._path.move_army(army=self, delta=+self.speed)
            elif path_direction.BACKWARDS:
                self._path.move_army(army=self, delta=-self.speed)
            else:
                raise BadDirectionException()

    def add_troop(self, troop: Troop):
        """
        Add a troop to this army.
        
        Args:
            troop: Troop to add
            
        Raises:
            BadAllegianceException: If troop has different allegiance
            AlreadyContainedException: If troop already in army
        """
        if troop.allegiance is not self._allegiance:
            raise BadAllegianceException()
        
        if troop in self._army_units:
            raise AlreadyContainedException()
        
        self._army_units.append(troop)
    
    @property
    def current_attributes(self) -> ArmyAttributes:
        """
        Get combined attributes of all troops in army.
        
        Speed is the slowest unit's speed. Morale is average. HP and damage are totaled.
        """
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
            total_damage_per_tick += army_unit.current_attributes.damage_per_tick
            total_morale += army_unit.current_attributes.morale

            if army_unit.current_attributes.speed < slowest_speed:
                slowest_speed = army_unit.current_attributes.speed

        average_morale = total_morale / len(self._army_units)
        assert 0 <= average_morale <= MAX_MORALE

        # Army speed is limited by slowest unit
        army_speed = slowest_speed

        return ArmyAttributes(
            hitpoints=total_hitpoints,
            speed=army_speed,
            damage_per_tick=total_damage_per_tick,
            morale=average_morale
        )
    
    @property
    def total_damage_per_tick(self) -> float:
        """Get total damage output of army."""
        return self.current_attributes.damage_per_tick

    @property
    def speed(self) -> int:
        """Get army movement speed (slowest unit)."""
        return self.current_attributes.speed

    @property
    def current_tick(self) -> int:
        """Get current game tick from empire."""
        return self._allegiance.current_tick
    
    @property
    def size(self) -> int:
        """Get total size of all troops in army."""
        return sum(army_unit.size for army_unit in self._army_units)
    
    def remove_dead_units(self):
        """Remove all dead troops from army."""
        self._army_units = [u for u in self._army_units if not u.is_dead]

    @property
    def troops(self) -> list[Troop]:
        """Get list of all troops in army."""
        return self._army_units

    @property
    def num_units(self) -> int:
        """Get number of troops in army."""
        return len(self._army_units)
    
    @property
    def allegiance(self) -> Optional[Empire]:
        """Get empire this army serves."""
        return self._allegiance
    
    def set_allegiance(self, empire: Empire):
        """Set the empire this army serves."""
        self._allegiance = empire
    
    def has_unit(self, army_unit: Troop) -> bool:
        """Return True if army contains the given troop."""
        return army_unit in self._army_units


def battle_next_tick(army1: Army, army2: Army):
    """
    Run one tick of battle between two armies.
    
    Armies deal damage to each other. Dead units are removed after combat.
    Units with low morale are targeted more frequently.
    
    Args:
        army1: First attacking army
        army2: Second attacking army
    """
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
    """
    Distribute damage across target army units based on morale bias.
    
    Units with low morale take disproportionate casualties (morale-based targeting).
    
    Args:
        target_army: Army receiving damage
        total_damage: Total damage to distribute
    """
    if target_army.num_units == 0 or total_damage <= 0:
        return

    # The lower the morale, the higher the chance of being hit
    weights = []
    for army_unit in target_army.troops:
        # Avoid division by zero; clamp morale to small epsilon
        weight = 1.0 / max(0.01, army_unit.current_morale)
        weights.append(weight)
    
    total_weight = sum(weights)
    if total_weight == 0:
        return

    # Apply proportionate damage
    for unit, weight in zip(target_army.troops, weights):
        portion = weight / total_weight
        dmg = total_damage * portion
        unit.apply_damage(dmg)


def armies_city_fight_next_tick(armies: list[Army], city: City):
    """
    Simulate one tick of battle between attacking armies and a defending city.
    
    Armies and city deal damage to each other. Dead units are removed.
    
    Args:
        armies: List of attacking armies (must share allegiance, must be in city)
        city: Defending city
        
    Raises:
        BadAllegianceException: If armies have different allegiance or are city's allegiance
        IllegalMoveException: If any army is not in the city
    """
    if not armies:
        return

    # Verify allegiance consistency and that each army is in city
    attacking_allegiance = armies[0].allegiance
    for army in armies:
        if army.allegiance is not attacking_allegiance:
            raise BadAllegianceException("All armies must share the same allegiance.")
        if army not in city.armies:
            raise IllegalMoveException("All armies must be present in the defending city.")
    
    if city.allegiance is attacking_allegiance:
        raise BadAllegianceException("City and attacking armies cannot share allegiance.")

    # Armies attack the city
    total_attack_damage = sum(army.current_attributes.damage_per_tick for army in armies)
    city.take_damage(dmg=total_attack_damage, attacker=attacking_allegiance)

    # City fights back
    if city.defense <= 0:
        return

    total_city_damage = city.defense
    total_hp = sum(a.current_attributes.hitpoints for a in armies)
    
    for army in armies:
        portion = army.current_attributes.hitpoints / total_hp if total_hp > 0 else 0
        _distribute_damage(army, total_city_damage * portion)