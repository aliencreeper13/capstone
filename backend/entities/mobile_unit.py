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
class CombatAttributes(GameObject):
    """
    Represents the combat attributes of an army or mobile unit.
    
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


class MobileUnit(Unit):
    """
    A generic unit that can move around from city to city.
    
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
    
    base_attributes: CombatAttributes
    
    def __init__(self, *args, **kwargs):
        """Initialize troop with base combat attributes and neutral morale."""
        super().__init__(*args, **kwargs)
        self._allegiance: Optional[Empire] = None
        
        self._base_attributes: CombatAttributes = self.base_attributes
        self._current_attributes: CombatAttributes = self.base_attributes
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
    def current_attributes(self) -> CombatAttributes:
        """Get current combat attributes (adjusted for morale)."""
        return self._current_attributes
    
    @property
    def current_morale(self) -> float:
        """Get current morale level."""
        return self._current_attributes.morale
    
    @property
    def max_attributes(self) -> CombatAttributes:
        """
        Get maximum possible attributes at max morale.
        
        Returns stats scaled up to reflect max morale condition.
        """
        return CombatAttributes(
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
    
