"""
MobileUnitGroup system for managing mobile units and combat mechanics.

MobileUnitGroups are generic containers for mobile units (both Troops and PassiveUnits).
They can move across the map, attack cities, and engage in combat with other groups.
All combat mechanics remain identical regardless of unit type composition.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional
import random

from ..core.constants import HALF_MORALE, MAX_MORALE
from ..core.gameobject import GameObject, public_client_property, private_client_property
from ..core.engine_utils import soft_isinstance
from ..systems.game_utils import new_value_given_morale
from ..gameplay.location import Path, PathDirection, GameNode
from .unit import Unit
from .mobile_unit import CombatAttributes, MobileUnit
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



class Troop(MobileUnit):
    """
    A military unit that can be added to mobile unit groups.
    
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
    pass

class MobileUnitGroup(GameObject):
    """
    A generic container for mobile units (troops, passive units, or mixed).
    
    MobileUnitGroups have combined attributes, can move on paths, occupy game nodes (cities),
    and engage in combat. Group speed is limited by slowest unit. All combat mechanics
    work identically whether the group contains troops, passive units, or a mix.
    
    Instance attributes:
        _allegiance: Empire this group serves (None for passive units in production)
        _mobile_units: List of mobile units (MobileUnit subclasses) in this group
        _gamenode: City or location this group is currently in
        _path: Path this group is currently traveling on
        _path_position: Position along current path (0.0-1.0)
    """
    
    def __init__(self, allegiance: Optional[Empire], initial_gamenode: GameNode):
        """Initialize empty mobile unit group for an empire."""
        super().__init__()
        self._allegiance: Optional[Empire] = allegiance
        self._mobile_units: list[MobileUnit] = []
        self._gamenode: Optional[GameNode] = initial_gamenode
        self._path: Optional[Path] = None
        self._path_position: Optional[float] = 0.0
        self._moving_on_path: bool = False # Indicates if the group is currently moving
        self._current_direction: Optional[PathDirection] = None # Current movement direction on path
        if allegiance is not None:
            allegiance.add_mobile_unit_group(self)
    @property
    def id(self) -> str:
        """Get unique identifier for this mobile unit group."""
        return f"{self.__class__.__name__}_{id(self)}"
    
    def start_moving(self, direction: Optional[PathDirection] = None):
        """
        Begin moving the mobile unit group along its current path
        Args:
            direction: Direction to move (FORWARDS or BACKWARDS). If None, continues in current direction.
        """
        if not self.on_path():
            return 
            # raise IllegalMoveException("Cannot start moving: Mobile unit group is not on a path.")
        
        self._moving_on_path = True
        if direction is not None:
            self._current_direction = direction

        print(f"Army {self.id} started moving {'forwards' if self._current_direction == PathDirection.FORWARDS else 'backwards'}.")

    def stop_moving(self):
        """Stop moving the mobile unit group along its current path."""
        self._moving_on_path = False
        print(f"Army {self.id} stopped moving.")

    def reverse_direction(self):
        """Reverse the current movement direction of the mobile unit group."""
        if not self.on_path():
            return 
            # raise IllegalMoveException("Cannot reverse direction: Mobile unit group is not on a path.")
        
        if self._current_direction == PathDirection.FORWARDS:
            self._current_direction = PathDirection.BACKWARDS
        elif self._current_direction == PathDirection.BACKWARDS:
            self._current_direction = PathDirection.FORWARDS
        else:
            raise BadDirectionException("Current direction is not set; cannot reverse.")
    def update(self, ticks: int = 1):
        """Update mobile unit group state each tick."""
        if not self._moving_on_path:
            return 
        if not self.on_path():
            return
        
        assert self._current_direction is not None, "Current direction must be set when moving."
        
        self.move_one_step_along_path(self._current_direction)

    def in_gamenode(self) -> bool:
        """Return True if army is currently in a game node (city)."""
        return self._gamenode is not None and isinstance(self._gamenode, GameNode)

    def on_path(self) -> bool:
        """Return True if army is currently on a path."""
        return self._path is not None and isinstance(self._path, Path)

    def get_on_path(self, path: Path):
        """Move army from current game node onto a path."""
        print("Attempting to get on path...")
        if self.in_gamenode():
            previous_gamenode = self._gamenode
            self._gamenode.remove_army(self)
            path.add_army(army=self, from_node=self._gamenode)
            self._path = path
            self._gamenode = None
            
            # determine which direction army should start off with
            if path.gamenode1 is previous_gamenode:
                self._current_direction = PathDirection.FORWARDS
                destination_gamenode = path.gamenode2
            else:
                self._current_direction = PathDirection.BACKWARDS
                destination_gamenode = path.gamenode1
            print(f"Army {self.id} departed from game node {previous_gamenode.coords} onto path which leads to {destination_gamenode.coords}.")
        else:
            print(f"Army {self.id} is not in a game node; cannot get on path.")
    def get_on_path_and_start_moving(self, path: Path):
        """Move army from current game node onto a path and start moving."""
        self.get_on_path(path)
        
        if self.on_path():
            self.start_moving()
        else:
            print(f"Army {self.id} could not get on path; cannot start moving.")
            

    def get_on_gamenode(self, gamenode: GameNode):
        """Move army from current path into a game node."""
        if self.on_path():
            self._path.remove_army(self)
            gamenode.add_army(self)
            self._gamenode = gamenode
            self._path = None
            self.stop_moving()
            print(f"Army {self.id} arrived at game node {gamenode.coords}.")

    def move_one_step_along_path(self, path_direction: PathDirection):
        """
        Move army along path in given direction.
        
        Args:
            path_direction: Direction to move (FORWARDS or BACKWARDS)
            
        Raises:
            BadDirectionException: If direction is invalid
            IllegalMoveException: If army is not on a path
        """
        if self.on_path():
            # In Path.move_army, if the army reaches the end, it is removed from the path and added to the game node
            if path_direction == PathDirection.FORWARDS:
                self._path.move_army(army=self, delta=+self.speed)
            elif path_direction == PathDirection.BACKWARDS:
                self._path.move_army(army=self, delta=-self.speed)
            else:
                raise BadDirectionException()
            print(f"Army {self.id} moved along path towards {'FORWARDS' if path_direction == PathDirection.FORWARDS else 'BACKWARDS'}.")

            

    def add_mobile_unit(self, mobile_unit: MobileUnit):
        """
        Add a mobile unit (troop or passive unit) to this group.
        
        Args:
            mobile_unit: MobileUnit to add
            
        Raises:
            BadAllegianceException: If unit has different allegiance
            AlreadyContainedException: If unit already in group
        """
        if mobile_unit.allegiance is not self._allegiance:
            raise BadAllegianceException()
        
        if mobile_unit in self._mobile_units:
            raise AlreadyContainedException()
        
        self._mobile_units.append(mobile_unit)
    
    def add_troop(self, troop: Troop):
        """
        Add a troop to this group (convenience method).
        
        Args:
            troop: Troop to add
        """
        self.add_mobile_unit(troop)
    
    @public_client_property
    def current_attributes(self) -> CombatAttributes:
        """
        Get combined attributes of all mobile units in group.
        
        Speed is the slowest unit's speed. Morale is average. HP and damage are totaled.
        Works with any combination of troops and passive units.
        """
        if len(self._mobile_units) == 0:
            return CombatAttributes(
                hitpoints=0,
                speed=0,
                damage_per_tick=0,
                morale=HALF_MORALE
            )
        
        total_hitpoints = 0
        total_damage_per_tick = 0
        total_morale = 0.0
        slowest_speed = float('inf')

        for mobile_unit in self._mobile_units:
            total_hitpoints += mobile_unit.current_attributes.hitpoints
            total_damage_per_tick += mobile_unit.current_attributes.damage_per_tick
            total_morale += mobile_unit.current_attributes.morale

            if mobile_unit.current_attributes.speed < slowest_speed:
                slowest_speed = mobile_unit.current_attributes.speed

        average_morale = total_morale / len(self._mobile_units)
        assert 0 <= average_morale <= MAX_MORALE

        # Group speed is limited by slowest unit
        group_speed = slowest_speed

        return CombatAttributes(
            hitpoints=total_hitpoints,
            speed=group_speed,
            damage_per_tick=total_damage_per_tick,
            morale=average_morale
        )
    
    @public_client_property
    def total_damage_per_tick(self) -> float:
        """Get total damage output of group."""
        return self.current_attributes.damage_per_tick

    @public_client_property
    def speed(self) -> int:
        """Get group movement speed (slowest unit)."""
        return self.current_attributes.speed

    @property
    def current_tick(self) -> int:
        """Get current game tick from empire."""
        return self._allegiance.current_tick
    
    @public_client_property
    def size(self) -> int:
        """Get total size of all mobile units in group."""
        return sum(unit.size for unit in self._mobile_units)
    
    def remove_dead_units(self):
        """Remove all dead units from group."""
        self._mobile_units = [u for u in self._mobile_units if not u.is_dead]

    @public_client_property
    def mobile_units(self) -> list[MobileUnit]:
        """Get list of all mobile units in group."""
        return self._mobile_units
    
    @public_client_property
    def troops(self) -> list[Troop]:
        """Get list of all troops in group (convenience property)."""
        return [u for u in self._mobile_units if isinstance(u, Troop)]

    @public_client_property
    def num_units(self) -> int:
        """Get number of mobile units in group."""
        return len(self._mobile_units)
    
    @public_client_property
    def allegiance(self) -> Optional[Empire]:
        """Get empire this group serves."""
        return self._allegiance
    
    def set_allegiance(self, empire: Empire):
        """Set the empire this group serves."""
        self._allegiance = empire
        self._allegiance.add_mobile_unit_group(self)
    
    def has_unit(self, mobile_unit: MobileUnit) -> bool:
        """Return True if group contains the given mobile unit."""
        return mobile_unit in self._mobile_units

    # TODO: Use/improve this method
    def split_off_units(self, units_to_split: list[MobileUnit]) -> MobileUnitGroup:
        """
        Split off specified mobile units into a new group.
        
        Args:
            units_to_split: List of mobile units to move to new group
            
        Returns:
            New MobileUnitGroup containing the split-off units
            
        Raises:
            BadAllegianceException: If any unit has different allegiance
            IllegalMoveException: If any unit is not in this group
        """
        new_group = MobileUnitGroup(allegiance=self._allegiance, initial_gamenode=self._gamenode)
        
        for unit in units_to_split:
            if unit.allegiance is not self._allegiance:
                raise BadAllegianceException()
            if unit not in self._mobile_units:
                raise IllegalMoveException("Unit to split is not in this group.")
            
            self._mobile_units.remove(unit)
            new_group.add_mobile_unit(unit)
        
        return new_group

    def merge(self, other_mobile_unit_group: MobileUnitGroup):
        """
        Merge another mobile unit group into this one.
        
        Args:
            other_mobile_unit_group: Group to merge into this one
            
        Raises:
            BadAllegianceException: If groups have different allegiance
        """
        if other_mobile_unit_group.allegiance is not self._allegiance:
            raise BadAllegianceException()
        
        for unit in other_mobile_unit_group.mobile_units:
            self.add_mobile_unit(unit)
        
        # TODO: Implement this
        # Clear the other group
        # other_mobile_unit_group._mobile_units.clear()

def battle_next_tick(group1: MobileUnitGroup, group2: MobileUnitGroup):
    """
    Run one tick of battle between two mobile unit groups.
    
    Groups deal damage to each other. Dead units are removed after combat.
    Units with low morale are targeted more frequently.
    Combat mechanics work identically regardless of whether groups contain troops, passive units, or a mix.
    
    Args:
        group1: First attacking mobile unit group
        group2: Second attacking mobile unit group
    """
    # Skip if either side is already dead
    if group1.num_units == 0 or group2.num_units == 0:
        return

    # Compute outgoing damage
    dmg1 = group1.current_attributes.damage_per_tick
    dmg2 = group2.current_attributes.damage_per_tick

    # Each side receives the other's damage
    _distribute_damage(group2, dmg1)  # group1 attacks group2
    _distribute_damage(group1, dmg2)  # group2 attacks group1

    # Remove dead units
    group1.remove_dead_units()
    group2.remove_dead_units()


def _distribute_damage(target_group: MobileUnitGroup, total_damage: float):
    """
    Distribute damage across target group units based on morale bias.
    
    Units with low morale take disproportionate casualties (morale-based targeting).
    Works with any combination of unit types.
    
    Args:
        target_group: Mobile unit group receiving damage
        total_damage: Total damage to distribute
    """
    if target_group.num_units == 0 or total_damage <= 0:
        return

    # The lower the morale, the higher the chance of being hit
    weights = []
    for mobile_unit in target_group.mobile_units:
        # Avoid division by zero; clamp morale to small epsilon
        weight = 1.0 / max(0.01, mobile_unit.current_morale)
        weights.append(weight)
    
    total_weight = sum(weights)
    if total_weight == 0:
        return

    # Apply proportionate damage
    for unit, weight in zip(target_group.mobile_units, weights):
        portion = weight / total_weight
        dmg = total_damage * portion
        unit.apply_damage(dmg)


def mobile_unit_groups_city_fight_next_tick(groups: list[MobileUnitGroup], city: City):
    """
    Simulate one tick of battle between attacking mobile unit groups and a defending city.
    
    Groups and city deal damage to each other. Dead units are removed.
    Combat mechanics work identically regardless of whether groups contain troops, passive units, or a mix.
    
    Args:
        groups: List of attacking mobile unit groups (must share allegiance, must be in city)
        city: Defending city
        
    Raises:
        BadAllegianceException: If groups have different allegiance or share city's allegiance
        IllegalMoveException: If any group is not in the city
    """
    if not groups:
        return

    # Verify allegiance consistency and that each group is in city
    attacking_allegiance = groups[0].allegiance
    for group in groups:
        if group.allegiance is not attacking_allegiance:
            raise BadAllegianceException("All groups must share the same allegiance.")
        if group not in city.armies:
            raise IllegalMoveException("All groups must be present in the defending city.")
    
    if city.allegiance is attacking_allegiance:
        raise BadAllegianceException("City and attacking groups cannot share allegiance.")

    # Groups attack the city
    total_attack_damage = sum(group.current_attributes.damage_per_tick for group in groups)
    city.take_damage(dmg=total_attack_damage, attacker=attacking_allegiance)

    # City fights back
    if city.defense <= 0:
        return

    total_city_damage = city.defense
    total_hp = sum(g.current_attributes.hitpoints for g in groups)
    
    for group in groups:
        portion = group.current_attributes.hitpoints / total_hp if total_hp > 0 else 0
        _distribute_damage(group, total_city_damage * portion)


# Backwards compatibility alias
def armies_city_fight_next_tick(armies: list[MobileUnitGroup], city: City):
    """Deprecated: Use mobile_unit_groups_city_fight_next_tick instead."""
    mobile_unit_groups_city_fight_next_tick(armies, city)


# Backwards compatibility class alias
Army = MobileUnitGroup
ArmyAttributes = CombatAttributes