"""
Effects system for applying game impacts (resources, morale, population changes, etc.).

Effects represent modifications to city state that can be applied each game tick.
They may be indefinite (building passive effects) or temporary (spell effects, debuffs).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil, floor
from typing import TYPE_CHECKING, Optional, Callable

from ..core.gameobject import GameObject
from .data import ExpendableCityResources, ExpendableEmpireResources

if TYPE_CHECKING:
    from ..entities.unit import Unit
    from ..entities.city import City


@dataclass
class Effect(GameObject):
    """
    Represents a game impact that can be applied to cities each tick.
    
    Effects can provide resources, modify morale, increase capacity, etc.
    Duration of 0 indicates indefinite effects (permanent while active).
    
    Attributes:
        duration_in_ticks: How many ticks this effect lasts (0 = indefinite)
        expendable_city_resources_per_tick: Resources generated/consumed per tick
        expendable_empire_resources_per_tick: Empire resources modified per tick
        expendable_city_resources_pct_increase: Percentage bonuses to city resource production
        expendable_empire_resources_pct_increase: Percentage bonuses to empire resources
        morale_per_tick: Morale change per tick
        raw_efficiency_per_tick: Empire efficiency change per tick (negative = corruption/inefficiency)
        city_base_defense_offered: Defensive bonus to city
        city_base_protection_offered: Protective bonus to city (absorption)
        city_hitpoint_regeneration_per_tick: HP recovered per tick
        expendable_city_resource_capacities_offered: Storage bonuses
        population_capacity_offered: Housing bonus
        new_people_per_tick: Birth rate modifier
        dead_people_per_tick: Death rate modifier
        capital_effect: Only applies when city is the capital
        specific_units_contingent_on: Effect only active if these units exist
        effect_id: Unique identifier for tracking effects
    """
    duration_in_ticks: int = 0

    expendable_city_resources_per_tick: ExpendableCityResources = field(
        default_factory=ExpendableCityResources
    )
    expendable_empire_resources_per_tick: ExpendableEmpireResources = field(
        default_factory=ExpendableEmpireResources
    )

    expendable_city_resources_pct_increase: ExpendableCityResources = field(
        default_factory=ExpendableCityResources
    )
    expendable_empire_resources_pct_increase: ExpendableEmpireResources = field(
        default_factory=ExpendableEmpireResources
    )

    theoretical_new_employable_per_tick: float = 0.0 # *Theoretical* new workers generated per tick. Actual workers per tick will be rounded to int

    raw_morale_per_tick: float = 0.0
    raw_efficiency_per_tick: float = 0.0  # Direct empire efficiency change per tick

    city_base_defense_offered: int = 0
    city_base_protection_offered: int = 0
    city_hitpoint_regeneration_per_tick: int = 0
    expendable_city_resource_capacities_offered: ExpendableCityResources = field(
        default_factory=ExpendableCityResources
    )
    population_capacity_offered: int = 0

    new_people_per_tick: int = 0
    dead_people_per_tick: int = 0
    max_lifespan_increase: int = 0  # Increases the maximum age population can reach

    capital_effect: bool = False
    specific_units_contingent_on: list[Unit] = field(default_factory=list)
    
    job_speedup_multiplier: float = 1.0  # Multiplier for job progress (>1.0 speeds up jobs)

    effect_id: Optional[int] = None

    # ========== Contingencies ==========
    # Arbitrary contingency check: effect only applies if this returns True
    # Example: lambda city: city._resources.food > 0
    contingency_check: Optional[Callable[[City], bool]] = None

    # ========== Dynamic Values (for Ongoing Effects) ==========
    # These allow effect values to change based on city state each tick.
    # If provided, these override the static values during effect application.
    # All should accept a City parameter and return the appropriate value type.
    
    # Dynamic per-tick resource changes (overrides expendable_city_resources_per_tick)
    dynamic_expendable_city_resources_per_tick: Optional[Callable[[City], ExpendableCityResources]] = None
    
    # Dynamic per-tick empire resource changes (overrides expendable_empire_resources_per_tick)
    dynamic_expendable_empire_resources_per_tick: Optional[Callable[[City], ExpendableEmpireResources]] = None

    # Dynamic per-tick new employable workers (overrides theoretical_new_employable_per_tick)
    dynamic_theoretical_new_employable_per_tick: Optional[Callable[[City], float]] = None
    
    # Dynamic per-tick morale change (overrides morale_per_tick)
    dynamic_morale_per_tick: Optional[Callable[[City], float]] = None
    
    # Dynamic per-tick efficiency change (overrides efficiency_per_tick)
    dynamic_raw_efficiency_per_tick: Optional[Callable[[City], float]] = None
    
    # Dynamic per-tick HP regeneration (overrides city_hitpoint_regeneration_per_tick)
    dynamic_city_hitpoint_regeneration_per_tick: Optional[Callable[[City], int]] = None
    
    # Dynamic per-tick new population (overrides new_people_per_tick)
    dynamic_new_people_per_tick: Optional[Callable[[City], int]] = None
    
    # Dynamic per-tick death rate (overrides dead_people_per_tick)
    dynamic_dead_people_per_tick: Optional[Callable[[City], int]] = None
    
    # Dynamic job speedup multiplier (overrides job_speedup_multiplier)
    dynamic_job_speedup_multiplier: Optional[Callable[[City], float]] = None

    def is_indefinite(self) -> bool:
        """Return True if this effect has infinite duration."""
        return self.duration_in_ticks == 0
    
    def is_universal(self) -> bool:
        """Return True if this is a universal effect (applies to all cities)."""
        return False
    
    def is_active(self) -> bool:
        """Return True if this effect is currently active (contingencies met)."""
        for unit_ in self.specific_units_contingent_on:
            if not unit_.is_active():
                return False
        return True
    
    def should_apply(self, city: City) -> bool:
        """
        Determine if this effect should apply to the given city.
        
        Checks both unit contingencies and arbitrary contingency_check.
        
        Args:
            city: The city to check contingencies for
            
        Returns:
            True if the effect should apply, False otherwise
        """
        # Check unit contingencies
        if not self.is_active():
            return False
        
        # Check arbitrary contingency if provided
        if self.contingency_check is not None:
            return self.contingency_check(city)
        
        return True
    
    def actual_new_employable_per_tick(self, city: City) -> int:
        """Get the actual new workers generated per tick, cannot exceed working-age population (rounded int)."""
        if self.dynamic_theoretical_new_employable_per_tick is not None:
            return ceil(self.dynamic_theoretical_new_employable_per_tick(city))
        else:
            return ceil(self.theoretical_new_employable_per_tick)
    
    def get_city_resources_per_tick(self, city: City) -> ExpendableCityResources:
        """Get the actual city resource changes for this tick, using dynamic values if available."""
        if self.dynamic_expendable_city_resources_per_tick is not None:
            return self.dynamic_expendable_city_resources_per_tick(city)
        return self.expendable_city_resources_per_tick
    
    def get_empire_resources_per_tick(self, city: City) -> ExpendableEmpireResources:
        """Get the actual empire resource changes for this tick, using dynamic values if available."""
        if self.dynamic_expendable_empire_resources_per_tick is not None:
            return self.dynamic_expendable_empire_resources_per_tick(city)
        return self.expendable_empire_resources_per_tick
    
    def get_raw_morale_per_tick(self, city: City) -> float:
        """Get the actual morale change for this tick, using dynamic values if available."""
        if self.dynamic_morale_per_tick is not None:
            return self.dynamic_morale_per_tick(city)
        return self.raw_morale_per_tick
    
    def get_raw_efficiency_per_tick(self, city: City) -> float:
        """Get the actual efficiency change for this tick, using dynamic values if available."""
        if self.dynamic_raw_efficiency_per_tick is not None:
            return self.dynamic_raw_efficiency_per_tick(city)
        return self.raw_efficiency_per_tick
    
    def get_city_hitpoint_regeneration_per_tick(self, city: City) -> int:
        """Get the actual HP regeneration for this tick, using dynamic values if available."""
        if self.dynamic_city_hitpoint_regeneration_per_tick is not None:
            return self.dynamic_city_hitpoint_regeneration_per_tick(city)
        return self.city_hitpoint_regeneration_per_tick
    
    def get_new_people_per_tick(self, city: City) -> int:
        """Get the actual population birth rate for this tick, using dynamic values if available."""
        if self.dynamic_new_people_per_tick is not None:
            return self.dynamic_new_people_per_tick(city)
        return self.new_people_per_tick
    
    def get_dead_people_per_tick(self, city: City) -> int:
        """Get the actual population death rate for this tick, using dynamic values if available."""
        if self.dynamic_dead_people_per_tick is not None:
            return self.dynamic_dead_people_per_tick(city)
        return self.dead_people_per_tick
    
    def get_job_speedup_multiplier(self, city: City) -> float:
        """Get the actual job speedup multiplier for this tick, using dynamic values if available."""
        if self.dynamic_job_speedup_multiplier is not None:
            return self.dynamic_job_speedup_multiplier(city)
        return self.job_speedup_multiplier


class UniversalEffect(Effect):
    """An effect that applies universally to all cities"""
    
    def is_universal(self) -> bool:
        return True


class OngoingEffect(Effect):
    """
    Effect with per-tick changes that recur while the effect is active.
    
    Ongoing effects apply changes every game tick, such as:
    - Resource generation/consumption per tick (expendable_city_resources_per_tick)
    - Morale changes per tick (raw_morale_per_tick)
    - HP regeneration per tick (city_hitpoint_regeneration_per_tick)
    - Population changes per tick (new_people_per_tick, dead_people_per_tick)
    - Empire resource changes per tick (expendable_empire_resources_per_tick)
    - Job speedup effects (job_speedup_multiplier)
    
    These effects persist for their duration and cease when the effect expires.
    """
    pass


class InstantEffect(Effect):
    """
    Effect with one-time changes applied upon activation or that persist as modifiers.
    
    Instant effects provide constant bonuses/penalties while active:
    - Defensive bonuses (city_base_defense_offered)
    - Protection bonuses (city_base_protection_offered)
    - Resource production multipliers (expendable_city_resources_pct_increase)
    - Empire resource multipliers (expendable_empire_resources_pct_increase)
    - Storage/housing capacities (expendable_city_resource_capacities_offered, population_capacity_offered)
    - Lifespan increases (max_lifespan_increase)
    
    These effects apply a constant modifier that changes the effective properties while the
    effect remains active, but don't generate changes on their own each tick. The effect
    is "instant" in the sense that it's a static modifier, not a per-tick generator.
    """
    pass


@dataclass
class EffectWithTicksLeft:
    """
    Tracks an effect and its remaining duration.
    
    Automatically manages duration countdown and expiration.
    
    Attributes:
        effect: The effect being applied
        ticks_left: Number of ticks remaining (0 = indefinite for indefinite effects)
    """
    effect: Effect
    ticks_left: int

    def progress(self):
        """Reduce remaining ticks by 1, minimum of 0."""
        self.ticks_left -= 1
        if self.ticks_left <= 0:
            self.ticks_left = 0

    def is_finished(self) -> bool:
        """
        Return True if this effect has expired.
        
        Indefinite effects (duration_in_ticks == 0) are never finished
        and will always return False unless manually removed.
        """
        if self.effect.is_indefinite():
            return False
        return self.ticks_left <= 0