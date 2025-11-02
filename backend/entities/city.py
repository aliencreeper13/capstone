"""
City: A player-controlled urban center for resource production and military operations.

Cities are the primary economic and military units in the game:
- Produce resources (food, timber, metal, wealth)
- House population that can work or serve in military
- Contain buildings that provide effects and generate resources
- Maintain morale, defense, hitpoints
- Can be captured or destroyed
- Allegiance to empires that control them

Bug fixes in this version:
1. ✅ DestructionJob initialization: Fixed in systems/job.py
2. ✅ Job level calculation: Now consistently uses job.level_upon_completion (line 403)
3. ✅ Worker lay-off logic: Fixed to use job.level_upon_completion instead of job_result.level (line 445)
"""

from __future__ import annotations

from math import ceil
from typing import TYPE_CHECKING, Optional
from queue import Queue
from datetime import datetime

from ..core.constants import (
    AUTOMATIC_FOOD_CONSUMPTION_EFFECT_ID,
    FOOD_CONSUMPTION_SENSITIVITY,
    LACK_OF_FOOD_MORALE_PENALTY,
    MAX_MORALE,
    MORALE_DEPLETION_DUE_TO_HUNGER_EFFECT_ID,
    MORALE_REVOLT_THRESHOLD,
)
from ..core.gameobject import (
    GameObject,
    client_property,
    private_client_property,
    public_client_property,
    HasAllegianceMixin,
)
from ..core.engine_utils import soft_isinstance

from ..systems.data import (
    ExpendableCityResources,
    Population,
    SocietalResources,
    ExpendableEmpireResources,
)
from ..systems.effects import Effect, EffectWithTicksLeft
from ..systems.job_requirements import JobRequirements
from ..systems.job import Job
from ..systems.game_utils import new_value_given_morale, bounded_stat_from_raw

from .unit import Unit
from .building import Building
from .army import Army, Troop

from ..gameplay.location import GameNode

from ..core.exceptions import (
    NotAssignedToGameException,
    NotEnoughWorkersException,
    RequirementsException,
)

if TYPE_CHECKING:
    from .empire import Empire


class City(GameNode, HasAllegianceMixin):
    """
    A city: player-controlled urban center for economy and warfare.
    
    Manages:
    - Resources (food, timber, metal, wealth) and capacities
    - Population (total, employable, employed)
    - Buildings and their effects
    - Job queue (construction, upgrades, unit creation)
    - Armies and military units
    - Morale, defense, and combat
    - Effects and their ticks remaining
    
    A city always belongs to exactly one GameNode location and can be
    allied with an Empire.
    """
    
    def __init__(self, coords: tuple[int, int], size: int = 5, morale: float = 50.0):
        """
        Initialize a new city at the given location.
        
        Args:
            coords: (x, y) coordinates on the world map
            size: Total space available for buildings
            morale: Initial morale (0-100, default 50)
        """
        super().__init__(coords=coords, size=size)
        
        # Resources and capacities
        self._resources: ExpendableCityResources = ExpendableCityResources()
        self._base_resource_capacities: ExpendableCityResources = ExpendableCityResources(
            food=100,
            timber=100,
            wealth=100,
            metal=100
        )

        # Population management
        self._societal_resources: SocietalResources = SocietalResources()
        self._employed_people: int = 0
        self._base_population_capacity: int = 1000

        # Defense and capture state
        self._base_defense = 100
        self._max_hitpoints: float = 100.0
        self._hitpoints: float = self._max_hitpoints
        self._empire_captured_by: Optional[Empire] = None

        # Allegiance to empire
        self._allegiance: Optional[Empire] = None

        # Raw morale (unbounded, 0 = baseline 50 displayed)
        # The morale parameter (0-100 display range) is converted to raw at initialization
        # If morale == 50, raw_morale == 0 (baseline)
        from ..systems.game_utils import raw_stat_from_bounded
        if morale == 50.0:
            self._raw_morale = 0.0  # Baseline case (most common)
        else:
            try:
                self._raw_morale = raw_stat_from_bounded(morale)
            except ValueError:
                # If morale is at extreme (0 or 100), use extreme raw value
                self._raw_morale = 1000.0 if morale > 50 else -1000.0
        
        self._gain_knowledge = 0

        # Buildings and jobs
        self._buildings: list[Building] = []
        self._running_jobs: list[Job] = []

        # Effects with time remaining
        self._effects_with_ticks_left: list[EffectWithTicksLeft] = []

        # Revolt system
        self._revolt_countdown: Optional[int] = None  # None = no revolt pending, >0 = ticks until revolt
        self._previous_allegiance: Optional[Empire] = None  # Track previous empire for revolts

        # Resource transfer system
        self._pending_transfers: list[dict] = []  # List of transfers: {target_city, resources, ticks_remaining}

        # Persistent effects initialization flags (for dynamic effects that should be added once)
        self._food_consumption_effect_added: bool = False
        self._hunger_penalty_effect_added: bool = False

        # Army for production (new units go here)
        self._production_army: Army = Army(allegiance=None)
        self._armies.append(self._production_army)
    
    # ========== Properties ==========

    @property
    def empire_captured_by(self) -> Optional[Empire]:
        """The empire that captured this city, if any."""
        return self._empire_captured_by

    def is_capital(self) -> bool:
        """Returns True if this city is the capital of its allegiant empire."""
        return self.allegiance.capital is self

    @public_client_property
    def allegiance(self) -> Optional[Empire]:
        """The empire this city belongs to."""
        return self._allegiance
    
    @private_client_property
    def autonomy(self) -> Optional[int]:
        """City autonomy permitted by the empire (0-100)."""
        if self.allegiance is None:
            return None
        return self.allegiance.autonomy
    
    @private_client_property
    def defense(self) -> float:
        """
        Total defensive strength of the city.
        
        Combines base defense, building effects, and allied armies.
        """
        total_defense = self._base_defense
        
        # Add defense from active effects
        for effect_with_ticks_left in self._effects_with_ticks_left:
            if not effect_with_ticks_left.is_finished():
                total_defense += effect_with_ticks_left.effect.city_base_defense_offered
        
        # Add defense from allied armies stationed here
        for army in self._armies:
            if army.allegiance is self.allegiance:
                total_defense += army.current_attributes.damage_per_tick
        
        return total_defense

    @private_client_property
    def size(self) -> int:
        """Total size of the city (space for buildings)."""
        return self._size

    @private_client_property
    def space_left(self) -> int:
        """Remaining space for new buildings."""
        return self._remaining_space()
    
    @private_client_property
    def hitpoints(self) -> float:
        """Current hitpoints of the city (0 = captured)."""
        return self._hitpoints
    
    def _regenerate_hitpoints(self, hitpoints: float) -> None:
        """Add hitpoints, clamping to maximum."""
        self._hitpoints = min(self._max_hitpoints, self._hitpoints + hitpoints)
    
    @private_client_property
    def protection(self) -> float:
        """
        Protection value (reduces incoming damage).
        
        Based on active effects and modified by city morale.
        """
        total_protection = 0
        for effect_with_ticks_left in self._effects_with_ticks_left:
            if not effect_with_ticks_left.is_finished():
                total_protection += effect_with_ticks_left.effect.city_base_protection_offered
        # Morale affects protection
        return new_value_given_morale(total_protection, self.morale)
    
    @private_client_property
    def expendable_resource_capacities(self) -> ExpendableCityResources:
        """Maximum resource capacity after accounting for all building effects."""
        resource_capacities = self._base_resource_capacities.copy()
        for effect_with_ticks_left in self._effects_with_ticks_left:
            if not effect_with_ticks_left.is_finished():
                resource_capacities.food += effect_with_ticks_left.effect.expendable_city_resource_capacities_offered.food
                resource_capacities.timber += effect_with_ticks_left.effect.expendable_city_resource_capacities_offered.timber
                resource_capacities.metal += effect_with_ticks_left.effect.expendable_city_resource_capacities_offered.metal
                resource_capacities.wealth += effect_with_ticks_left.effect.expendable_city_resource_capacities_offered.wealth
        return resource_capacities
    
    @private_client_property
    def population_limit(self) -> int:
        """Maximum population capacity after accounting for housing effects."""
        total_population_capacity = self._base_population_capacity
        for effect_with_ticks_left in self._effects_with_ticks_left:
            if not effect_with_ticks_left.is_finished():
                total_population_capacity += effect_with_ticks_left.effect.population_capacity_offered

        return total_population_capacity
    
    @private_client_property
    def knowledge(self) -> Optional[int]:
        """Empire-wide knowledge (forwarded from empire if allegiant)."""
        if self.allegiance is None:
            return None
        return self.allegiance.knowledge
    
    @private_client_property
    def expendable_city_resource_pct_increase(self) -> ExpendableCityResources:
        """Percentage increase to resource production from all active effects."""
        factor: ExpendableCityResources = ExpendableCityResources() + 1  # All attributes = 1
        for effect_with_ticks_left in self._effects_with_ticks_left:
            if effect_with_ticks_left.is_finished():
                continue
            effect = effect_with_ticks_left.effect
            factor *= ((effect.expendable_city_resources_pct_increase / 100) + 1)
        pct_increase = (factor * 100) - 1
        return pct_increase
    
    @private_client_property
    def expendable_city_resource_factor(self) -> ExpendableCityResources:
        """Multiplier factor for resource production (percentage increase as decimal factor)."""
        return self.expendable_city_resource_pct_increase / 100 + 1
    
    def change_knowledge(self, value: int) -> None:
        """Change empire knowledge by the given amount."""
        if self.allegiance:
            self.allegiance.change_knowledge(value)

    @private_client_property
    def total_population(self) -> int:
        """Total population across all age groups."""
        return self._societal_resources.population.total()
    
    @private_client_property
    def employable_population(self) -> int:
        """Population that is available to work (working age but not employed)."""
        return self._societal_resources.employable_population
    
    @public_client_property
    def current_tick(self) -> Optional[int]:
        """Current game tick from the empire's game engine."""
        if self.allegiance is None:
            return None
        return self.allegiance.game.current_tick

    @private_client_property
    def morale(self) -> float:
        """
        City morale (0-100 displayed). Low morale reduces production and risks revolts.
        
        This is a computed property derived from the unbounded raw_morale value.
        The computation uses a hyperbolic tangent curve to convert raw → displayed.
        """
        return bounded_stat_from_raw(self._raw_morale)

    @morale.setter
    def morale(self, new_raw_morale_change: float) -> None:
        """
        Modify raw morale by a given amount (not setting it to an absolute value).
        
        This method adds to raw_morale, which then gets converted to displayed morale
        via the getter. The revolt system checks the displayed morale value.
        
        Args:
            new_raw_morale_change: Amount to add/subtract from raw_morale
        """
        from ..core.constants import REVOLT_COUNTDOWN_WHEN_MORALE_ZERO
        
        old_displayed_morale = self.morale  # Get current displayed value
        self._raw_morale += new_raw_morale_change
        new_displayed_morale = self.morale  # Get new displayed value
        
        # Start revolt countdown if displayed morale drops below threshold
        if new_displayed_morale < MORALE_REVOLT_THRESHOLD and old_displayed_morale >= MORALE_REVOLT_THRESHOLD and self._revolt_countdown is None:
            self._revolt_countdown = REVOLT_COUNTDOWN_WHEN_MORALE_ZERO
        
        # Cancel revolt countdown if morale recovers above threshold
        elif new_displayed_morale >= MORALE_REVOLT_THRESHOLD and old_displayed_morale < MORALE_REVOLT_THRESHOLD and self._revolt_countdown is not None:
            self._revolt_countdown = None
    
    def add_raw_morale(self, amount: float) -> None:
        """
        Add morale to the city by modifying raw morale (or subtract to reduce morale).
        
        This method modifies the unbounded raw_morale value, which is then converted
        to a displayed morale (0-100) using a hyperbolic tangent curve. Higher displayed
        morale means better city mood and production. Low morale causes revolts.
        
        This is the primary method for modifying morale; it's used by building effects
        and other game mechanics. Effects specify raw_morale_per_tick which directly adds to
        raw_morale.
        
        Args:
            amount: The amount to add to raw_morale (can be negative for morale penalties)
                   Due to the conversion curve, adding/subtracting from raw_morale has
                   diminishing returns near the extremes, preventing easy saturation.
        """
        from ..core.constants import REVOLT_COUNTDOWN_WHEN_MORALE_ZERO
        
        old_displayed_morale = self.morale  # Get current displayed value
        self._raw_morale += float(amount)
        new_displayed_morale = self.morale  # Get new displayed value
        
        # Start revolt countdown if displayed morale drops below threshold
        if new_displayed_morale < MORALE_REVOLT_THRESHOLD and old_displayed_morale >= MORALE_REVOLT_THRESHOLD and self._revolt_countdown is None:
            self._revolt_countdown = REVOLT_COUNTDOWN_WHEN_MORALE_ZERO
        
        # Cancel revolt countdown if morale recovers above threshold
        elif new_displayed_morale >= MORALE_REVOLT_THRESHOLD and old_displayed_morale < MORALE_REVOLT_THRESHOLD and self._revolt_countdown is not None:
            self._revolt_countdown = None

    # ========== Public Resource Accessors (for external systems) ==========

    def get_food(self) -> float:
        """Get current food resources (public accessor)."""
        return self._resources.food
    
    def get_timber(self) -> float:
        """Get current timber resources (public accessor)."""
        return self._resources.timber
    
    def get_metal(self) -> float:
        """Get current metal resources (public accessor)."""
        return self._resources.metal
    
    def get_wealth(self) -> float:
        """Get current wealth resources (public accessor)."""
        return self._resources.wealth

    def get_population_data(self) -> Population:
        """Get population object for detailed demographic analysis (public accessor)."""
        return self._societal_resources.population

    def get_current_population(self) -> int:
        """Get total population across all age groups (public accessor)."""
        return self._societal_resources.population.total()

    def get_employable_population(self) -> int:
        """Get population available to work (public accessor)."""
        return self._societal_resources.employable_population

    # ========== Allegiance and Status ==========

    def set_allegiance(self, allegiance: Empire) -> None:
        """Assign this city to an empire."""
        self._allegiance = allegiance
        self._production_army.set_allegiance(empire=allegiance)

    def declare_independence(self) -> None:
        """Remove this city from any empire allegiance."""
        self._allegiance = None

    # ========== Population Management ==========

    def _employ_people(self, num_people: int) -> None:
        """
        Employ workers for a job.
        
        Args:
            num_people: Number of workers to employ
            
        Raises:
            NotEnoughWorkersException: If not enough employable population
        """
        if self._societal_resources.employable_population - num_people < 0:
            raise NotEnoughWorkersException(
                f"Not enough workers: have {self._societal_resources.employable_population}, "
                f"need {num_people}"
            )
        self._societal_resources.employable_population -= num_people
        self._societal_resources.employed_population += num_people

    def _lay_off_workers(self, num_people: int) -> None:
        """
        Release workers from a completed job.
        
        Args:
            num_people: Number of workers to release
            
        Raises:
            NotEnoughWorkersException: If not enough employed population
        """
        if self._societal_resources.employed_population - num_people < 0:
            raise NotEnoughWorkersException(
                f"Not enough employed workers to lay off: have {self._societal_resources.employed_population}, "
                f"need {num_people}"
            )
        self._societal_resources.employable_population += num_people
        self._societal_resources.employed_population -= num_people

    def increase_population(self, new_people: int) -> None:
        """
        Increase the total population of the city.
        
        New population is added to the youngest age group (age 0, newborns).
        Population respects the city's capacity limit.
        
        Args:
            new_people: Number of people to add (must be > 0)
        """
        if new_people <= 0:
            return
        
        # Don't exceed population capacity
        current_total = self.total_population
        available_capacity = self.population_limit - current_total
        people_to_add = min(new_people, available_capacity)
        
        if people_to_add > 0:
            self._societal_resources.population.add_population(people_to_add, age_group=0)

    # ========== Space and Buildings ==========

    def _remaining_space(self) -> int:
        """Calculate remaining space for new buildings."""
        total_occupied_space: int = 0
        for building in self._buildings:
            total_occupied_space += building.size
        return self._size - total_occupied_space
    
    def _add_building(self, building: Building) -> None:
        """
        Add a completed building to the city.
        
        When a building is added, its effects are applied, including any max_lifespan_increase
        that is applied immediately to the population (not recalculated each tick).
        
        Args:
            building: The building to add
        """
        assert self._remaining_space() > 0, "No space for new building"
        assert building not in self._buildings, "Building already in city"

        self._buildings.append(building)
        self._size -= building.size
        building.set_city(self)
        
        # Apply building's passive effects
        self.add_effect(effect=building.effect)
        
        # Apply max_lifespan_increase immediately (not per-tick)
        if building.effect.max_lifespan_increase > 0:
            self._societal_resources.population.max_lifespan += building.effect.max_lifespan_increase

    def _destroy_building(self, building: Building) -> None:
        """
        Destroy a building and reclaim its space.
        
        When a building is destroyed, any max_lifespan_increase it provided is removed
        from the population (to prevent exploiting building destruction/reconstruction).
        
        Args:
            building: The building to destroy
        """
        # Remove max_lifespan_increase if this building provided it
        if building.effect.max_lifespan_increase > 0:
            self._societal_resources.population.max_lifespan -= building.effect.max_lifespan_increase
        
        building.set_inactive()
        self._size += building.size
        self._buildings.remove(building)

    # ========== Army and Units ==========

    def _add_army_unit(self, army_unit: Troop) -> None:
        """
        Add a newly created military unit to the production army.
        
        Args:
            army_unit: The troop to add
        """
        assert not self._production_army.has_unit(army_unit=army_unit), "Unit already in production army"
        army_unit.set_allegiance(empire=self.allegiance)
        self._production_army.add_troop(troop=army_unit)

    def units_of_subclass_active_in_city(self, unit_class: type, minimum_level: int = 0) -> int:
        """
        Count active units of a specific type in this city.
        
        Useful for checking if job prerequisites are met (e.g., "has active Barracks").
        
        Args:
            unit_class: The unit type to count
            minimum_level: Minimum level of units to count
            
        Returns:
            Number of active units matching criteria
        """
        count = 0
        for building in self._buildings:
            if isinstance(building, unit_class) and building.is_active() and building.level >= minimum_level:
                count += 1
        return count

    # ========== Resources ==========

    def _clamp_resource(self, current_value: float, capacity: float, min_value: float = 0.0) -> float:
        """Helper to clamp a resource between min_value and capacity."""
        return max(min_value, min(current_value, capacity))
    
    def _apply_resource_delta(self, delta_resources: ExpendableCityResources, clamp_to_capacity: bool = True) -> None:
        """
        Internal helper to apply resource changes with optional clamping.
        
        This consolidates the common logic for all resource mutations to prevent DRY violations.
        
        Args:
            delta_resources: The amount to change each resource by
            clamp_to_capacity: If True, clamp to [0, capacity]. If False, clamp to [0, inf)
        """
        self._resources.food += delta_resources.food
        self._resources.timber += delta_resources.timber
        self._resources.metal += delta_resources.metal
        self._resources.wealth += delta_resources.wealth

        # Apply clamping rules
        if clamp_to_capacity:
            capacities = self.expendable_resource_capacities
            self._resources.food = self._clamp_resource(self._resources.food, capacities.food)
            self._resources.timber = self._clamp_resource(self._resources.timber, capacities.timber)
            self._resources.metal = self._clamp_resource(self._resources.metal, capacities.metal)
            self._resources.wealth = self._clamp_resource(self._resources.wealth, capacities.wealth)
        else:
            # Just clamp to non-negative
            self._resources.food = max(0.0, self._resources.food)
            self._resources.timber = max(0.0, self._resources.timber)
            self._resources.metal = max(0.0, self._resources.metal)
            self._resources.wealth = max(0.0, self._resources.wealth)
    
    def change_resources(self, delta_city_resources: ExpendableCityResources) -> None:
        """
        Apply resource changes from effects, buildings, etc. with capacity limits.
        
        Resources are clamped to [0, capacity]. This is used for resource generation
        and consumption that respects storage limits.
        
        Args:
            delta_city_resources: The amount to change each resource by
        """
        self._apply_resource_delta(delta_city_resources, clamp_to_capacity=True)

    def expend_city_resources(self, city_resources: ExpendableCityResources) -> None:
        """
        Consume resources from the city (for jobs, construction, etc.).
        
        Resources cannot go below 0, but can exceed capacity temporarily.
        Resources will be clamped to capacity on the next effect tick.
        
        Args:
            city_resources: The amount of each resource to consume
        """
        self._apply_resource_delta(city_resources, clamp_to_capacity=False)

    def change_empire_resources(self, empire_resources: ExpendableEmpireResources) -> None:
        """
        Apply empire-wide resource changes.
        
        Empire resources (efficiency, knowledge, stability) are managed at the empire
        level, not city level. This forwards changes to the empire if this city is
        allegiant. Phase 5: Uses efficiency-based system (corruption = 100 - efficiency).
        
        Args:
            empire_resources: The empire resource changes to apply
        """
        if self.allegiance is not None:
            # Forward empire resource changes to the empire
            # Phase 5: Using efficiency-based system (corruption = 100 - efficiency)
            self.allegiance.add_knowledge(empire_resources.knowledge)
            self.allegiance.add_raw_efficiency(empire_resources.efficiency)

    # ========== Effects ==========

    def _accumulate_active_effect_property(self, getter_func) -> float:
        """
        Generic helper to sum a property across all active effects.
        
        This reduces DRY violations when calculating total bonuses from effects.
        
        Args:
            getter_func: A callable that takes an effect and returns the property value
            
        Returns:
            Sum of the property across all active effects
        """
        total = 0.0
        for effect_with_ticks_left in self._effects_with_ticks_left:
            if not effect_with_ticks_left.is_finished():
                total += getter_func(effect_with_ticks_left.effect)
        return total

    def add_effect(self, effect: Effect) -> None:
        """
        Add an effect to this city with a set duration.
        
        If an effect has an effect_id, it replaces any existing effect with the same ID
        (only one effect with a given ID can be active at once).
        
        Args:
            effect: The effect to add
        """
        # Remove any existing effects with the same ID
        if effect.effect_id is not None:
            for i, effect_with_ticks_left in enumerate(self._effects_with_ticks_left):
                if effect_with_ticks_left.effect.effect_id == effect.effect_id:
                    self._effects_with_ticks_left[i] = None
            # Clean up None markers
            while None in self._effects_with_ticks_left:
                self._effects_with_ticks_left.remove(None)
        
        self._effects_with_ticks_left.append(EffectWithTicksLeft(
            effect=effect,
            ticks_left=effect.duration_in_ticks
        ))

    def _apply_effect(self, effect: Effect, ticks_elapsed: int = 1) -> None:
        """
        Apply an effect to this city for a single tick.
        
        Effects modify resources, morale, capacities, and other city properties.
        Capital-only effects are skipped if this is not the capital.
        Contingencies are checked before applying the effect.
        
        Args:
            effect: The effect to apply
            ticks_elapsed: Number of ticks to apply for (default 1)
        """
        # Skip capital-exclusive effects if this is not the capital
        if effect.capital_effect and not self.is_capital():
            return
        
        # Check contingencies - if effect shouldn't apply, return early
        if not effect.should_apply(self):
            return

        # Apply resource changes (using dynamic values if available)
        self.change_resources(
            effect.get_city_resources_per_tick(self) * ticks_elapsed * self.expendable_city_resource_factor
        )

        # Apply empire resource changes (including knowledge)
        self.change_empire_resources(effect.get_empire_resources_per_tick(self) * ticks_elapsed)
        
        # Apply morale changes (setter automatically clamps to [0, MAX_MORALE])
        self._raw_morale += effect.get_raw_morale_per_tick(self) * ticks_elapsed
        
        # Apply efficiency changes (if allegiant to an empire)
        efficiency_per_tick = effect.get_efficiency_per_tick(self)
        if efficiency_per_tick != 0.0 and self.allegiance is not None:
            self.allegiance.add_raw_efficiency(efficiency_per_tick * ticks_elapsed)

    def _apply_all_effects(self) -> None:
        """
        Process all active effects for this tick, decrementing their durations.
        
        When effects finish, they are removed from the active list.
        """
        effects_to_remove = []
        
        for i, effect_with_ticks_left in enumerate(self._effects_with_ticks_left):
            effect = effect_with_ticks_left.effect
            self._apply_effect(effect, ticks_elapsed=1)
            
            # Decrement ticks remaining
            effect_with_ticks_left.ticks_left -= 1
            
            # Mark finished effects for removal
            if effect_with_ticks_left.is_finished():
                effects_to_remove.append(i)
        
        # Remove finished effects in reverse order to maintain indices
        for i in reversed(effects_to_remove):
            del self._effects_with_ticks_left[i]

    # ========== Jobs ==========

    def add_job(self, job: Job) -> tuple[bool, str, list[str]]:
        """
        Add a job to the city's queue if requirements are met.
        
        Checks that:
        - Required units are active
        - Required resources are available
        - Enough workers are available
        
        All requirements are checked (not just the first failure), allowing
        comprehensive error reporting.
        
        Args:
            job: The job to add
            
        Returns:
            Tuple of (success: bool, message: str, failures: list[str])
            - success: True if job was added, False otherwise
            - message: User-friendly description of result
            - failures: List of requirement failures (empty if success)
            
        Raises:
            RequirementsException: Only for backwards compatibility if called with exception handling
        """
        from ..gameplay.events import GameEvent
        
        def check_requirements(job: Job) -> tuple[bool, list[str]]:
            """
            Check all job requirements and collect any failures.
            
            Returns:
                Tuple of (all_met: bool, failures: list[str])
            """
            requirements: JobRequirements = job.requirements
            level = job.level_upon_completion
            failures: list[str] = []

            # Check specific units are active
            specific_units_contingent_on = requirements.specific_units_contingent_on
            for unit_ in specific_units_contingent_on:
                if not unit_.is_active():
                    failures.append(f"Required unit {unit_.name} is not active")
                
            # Check unit types are available
            for contingent_on_info in requirements.unit_types_contingent_on:
                num_satisfying_units = self.units_of_subclass_active_in_city(
                    unit_class=contingent_on_info.unit_class,
                    minimum_level=contingent_on_info.minimum_level_needed
                )
                if num_satisfying_units <= 0:
                    failures.append(f"Need {contingent_on_info.unit_class.__name__} units (level {contingent_on_info.minimum_level_needed}+)")

            # Check resources are available
            food_needed = requirements.food(level=level)
            timber_needed = requirements.timber(level=level)
            wealth_needed = requirements.wealth(level=level)
            metal_needed = requirements.metal(level=level)
            
            if self._resources.food < food_needed:
                failures.append(f"Need {food_needed:.1f} food, have {self._resources.food:.1f}")
            if self._resources.timber < timber_needed:
                failures.append(f"Need {timber_needed:.1f} timber, have {self._resources.timber:.1f}")
            if self._resources.wealth < wealth_needed:
                failures.append(f"Need {wealth_needed:.1f} wealth, have {self._resources.wealth:.1f}")
            if self._resources.metal < metal_needed:
                failures.append(f"Need {metal_needed:.1f} metal, have {self._resources.metal:.1f}")

            # Check workers are available
            workers_needed = requirements.workers_needed(level=level)
            if self.employable_population < workers_needed:
                failures.append(f"Need {workers_needed} workers, have {self.employable_population}")
            
            return len(failures) == 0, failures

        # Check all requirements
        requirements_met, failures = check_requirements(job)
        
        # Record game event
        if self.allegiance is not None:
            job_name = job.result.__name__ if hasattr(job.result, '__name__') else str(job.result)
            
            if requirements_met:
                # Add job successfully
                level = job.level_upon_completion
                self.expend_city_resources(job.requirements.city_resources(level=level))
                self._employ_people(job.requirements.workers_needed(level=level))
                self._running_jobs.append(job)
                
                event = GameEvent(
                    type="custom",
                    timestamp=datetime.now(),
                    source="City",
                    description=f"Job started in {self.name}: {job_name}",
                    data={"city_name": self.name, "job_type": job_name, "status": "started"}
                )
                message = f"✓ Started job: {job_name}"
            else:
                # Job failed due to missing requirements
                event = GameEvent(
                    type="custom",
                    timestamp=datetime.now(),
                    source="City",
                    description=f"Job submission failed in {self.name}: {', '.join(failures)}",
                    data={
                        "city_name": self.name,
                        "job_type": job_name,
                        "status": "failed",
                        "reasons": failures
                    }
                )
                message = f"✗ Cannot start job: {', '.join(failures)}"
            
            self.allegiance.record_event(event)
        else:
            # No allegiance, just add the job if requirements are met
            if requirements_met:
                level = job.level_upon_completion
                self.expend_city_resources(job.requirements.city_resources(level=level))
                self._employ_people(job.requirements.workers_needed(level=level))
                self._running_jobs.append(job)
                message = "✓ Job started"
            else:
                message = f"✗ Cannot start job: {', '.join(failures)}"
        
        return requirements_met, message, failures

    def take_damage(self, dmg: float, attacker: Empire) -> None:
        """
        Apply damage to the city from an attacking empire.
        
        Uses a fractional absorption model where protection reduces damage.
        When hitpoints reach 0, the city is captured.
        
        Args:
            dmg: Damage amount to apply
            attacker: The empire dealing the damage
        """
        k = 100  # Balance constant for absorption model
        absorbed_fraction = self.protection / (self.protection + k)
        effective_dmg = dmg * (1 - absorbed_fraction)
        self._hitpoints = max(0, self.hitpoints - effective_dmg)
        
        if self._hitpoints == 0:
            self._empire_captured_by = attacker
            attacker.capture_city(self)

    def update(self) -> None:
        """
        Process one game tick for this city.
        
        Handles:
        - Job progression and completion
        - Worker lay-off from finished jobs
        - Population aging, death, and growth
        - Automatic resource production and consumption
        - Morale degradation baseline
        - Effect processing (which applies morale gains, buffs, etc.)
        """
        from ..core.constants import (
            FOOD_CONSUMPTION_SENSITIVITY, LACK_OF_FOOD_MORALE_PENALTY,
            BASELINE_MORALE_DEGRADATION, POPULATION_GROWTH_BASE_RATE,
            POPULATION_GROWTH_MORALE_THRESHOLD, POPULATION_GROWTH_MORALE_BONUS,
            POPULATION_DEATH_RATE_WHEN_NO_FOOD, AUTOMATIC_FOOD_CONSUMPTION_EFFECT_ID,
            MORALE_DEPLETION_DUE_TO_HUNGER_EFFECT_ID
        )
        
        print(self._resources)
        
        # ===== POPULATION MANAGEMENT =====
        # Age population and handle deaths
        deaths = self._societal_resources.population.age_population()
        if deaths > 0:
            print(f"{self.name}: {deaths} people died from old age")
        
        # ===== POPULATION DYNAMICS =====
        # Use the new population dynamics system for comprehensive population changes
        from ..systems.population_dynamics import PopulationDynamics
        
        # Calculate all population changes
        population_changes = PopulationDynamics.calculate_population_change(self)
        
        # Apply the changes
        PopulationDynamics.apply_population_changes(self, population_changes)
        
        # Print population report (can be disabled in production)
        if (population_changes['births'] > 0 or population_changes['net_change'] != 0 or
            population_changes['deaths_old_age'] > 0 or population_changes['emigration'] > 0):
            PopulationDynamics.print_population_report(self, population_changes)
        
        # ===== JOB PROGRESSION =====
        # Calculate job speedup multiplier from active effects (subsidies)
        job_speedup_multiplier = 1.0
        for effect_with_ticks_left in self._effects_with_ticks_left:
            if effect_with_ticks_left is not None and effect_with_ticks_left.effect.job_speedup_multiplier > 1.0:
                # Take the maximum speedup multiplier if multiple subsidies are active
                job_speedup_multiplier = max(job_speedup_multiplier, effect_with_ticks_left.effect.job_speedup_multiplier)
        
        # Progress all running jobs with the speedup multiplier
        for job in self._running_jobs:
            job.progress(ticks_elapsed=job_speedup_multiplier)
            if job.is_finished():
                job_result = job.result
                
                # Verify job result is a valid unit
                assert soft_isinstance(job_result, Unit), "Job result must be a Unit"
                
                # Handle different job result types
                if isinstance(job_result, Building):
                    if job.is_upgrade:
                        pass  # Upgrades handled by job system
                    else:
                        assert job_result is not None
                        self._add_building(job_result)
                elif isinstance(job_result, Troop):
                    self._add_army_unit(job_result)

                print("Finished job!")
                self._running_jobs.remove(job)

                # **BUG FIX**: Use job.level_upon_completion instead of job_result.level
                # (job_result doesn't have a level attribute; we use the job's level)
                self._lay_off_workers(job.requirements.workers_needed(level=job.level_upon_completion))
                
                print("Buildings:", self._buildings)

        # ===== RESOURCE CONSUMPTION & EFFECTS =====
        # Baseline morale degradation (natural baseline that effects balance out)
        self.add_effect(effect=Effect(
            duration_in_ticks=1,
            raw_morale_per_tick=-BASELINE_MORALE_DEGRADATION,
            effect_id=999  # Reserved for morale degradation
        ))

        # ===== REVOLT PROCESSING =====
        self._process_revolt_countdown()
        
        # ===== RESOURCE TRANSFERS =====
        self._process_resource_transfers()

        # Apply all active effects
        self._apply_all_effects()

    # ========== Revolt System ==========

    def _process_revolt_countdown(self) -> None:
        """
        Process the revolt countdown.
        
        Decrements countdown each tick. When it reaches 0, the city revolts.
        """
        if self._revolt_countdown is not None and self._revolt_countdown > 0:
            self._revolt_countdown -= 1
            
            if self._revolt_countdown == 0:
                self._trigger_revolt()
    
    def _trigger_revolt(self) -> None:
        """
        Trigger a city revolt.
        
        Transfers city to either:
        1. Previous empire that controlled it (if still alive)
        2. A new AI empire (creating one if this is first revolt)
        """
        if self.allegiance is None:
            return  # Can't revolt without an empire
        
        print(f"✗ REVOLT: {self.name} has revolted against {self.allegiance.allegiance.name if hasattr(self.allegiance.allegiance, 'name') else 'their empire'}!")
        
        # Determine new empire: try previous allegiance, else create AI empire
        if self._previous_allegiance is not None:
            new_empire = self._previous_allegiance
            print(f"  → {self.name} rejoins {new_empire.allegiance.name if hasattr(new_empire.allegiance, 'name') else 'the previous empire'}")
        else:
            # Create new AI empire
            from .ideology import NeutralIdeology
            new_empire = Empire(autonomy=50, capital_city=self, ideology=NeutralIdeology())
            new_empire.assign_to_game(self.allegiance.game)
            print(f"  → {self.name} becomes capital of new AI empire")
        
        # Store current allegiance as previous before transfer
        self._previous_allegiance = self.allegiance
        
        # Transfer city to new empire
        old_empire = self.allegiance
        new_empire.add_city(self)
        
        # Reset revolt countdown
        self._revolt_countdown = None
    
    def set_revolt_countdown(self, ticks: int) -> None:
        """
        Manually set the revolt countdown (for testing or special events).
        
        Args:
            ticks: Number of ticks until revolt (0 for instant revolt)
        """
        self._revolt_countdown = ticks
    
    def get_revolt_countdown(self) -> Optional[int]:
        """Get current revolt countdown (-1 = no countdown, 0+ = ticks remaining)."""
        return self._revolt_countdown

    # ========== Resource Transfer System ==========

    def transfer_resources_to_city(self, 
                                   target_city: "City", 
                                   resources: ExpendableCityResources) -> tuple[bool, str]:
        """
        Transfer resources from this city to a target city.
        
        The transfer incurs a wealth cost based on distance and takes multiple ticks
        to complete based on distance.
        
        Args:
            target_city: Destination city
            resources: Resources to transfer
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        from ..core.constants import RESOURCE_TRANSFER_WEALTH_COST_PER_TILE, RESOURCE_TRANSFER_TICKS_PER_TILE
        
        # Calculate distance (Chebyshev/Chessboard distance)
        dx = abs(self.coords[0] - target_city.coords[0])
        dy = abs(self.coords[1] - target_city.coords[1])
        distance = max(dx, dy)
        
        # Calculate costs
        wealth_cost = distance * RESOURCE_TRANSFER_WEALTH_COST_PER_TILE
        transfer_ticks = max(1, int(distance * RESOURCE_TRANSFER_TICKS_PER_TILE))
        
        # Check if this city has enough wealth
        if self._resources.wealth < wealth_cost:
            return False, f"Insufficient wealth for transfer. Need {wealth_cost}, have {self._resources.wealth}"
        
        # Deduct wealth cost
        self.expend_city_resources(ExpendableCityResources(wealth=wealth_cost))
        
        # Create transfer record
        transfer = {
            'target_city': target_city,
            'resources': resources,
            'ticks_remaining': transfer_ticks,
            'distance': distance
        }
        self._pending_transfers.append(transfer)
        
        return True, f"Transfer initiated. Will arrive in {transfer_ticks} ticks."
    
    def _process_resource_transfers(self) -> None:
        """
        Process active resource transfers.
        
        Decrements transfer timers and completes transfers when timer reaches 0.
        """
        completed_transfers = []
        
        for transfer in self._pending_transfers:
            transfer['ticks_remaining'] -= 1
            
            if transfer['ticks_remaining'] <= 0:
                # Transfer complete - add resources to target city
                target_city = transfer['target_city']
                resources = transfer['resources']
                
                target_city.change_resources(resources)
                completed_transfers.append(transfer)
                
                print(f"✓ Transfer complete: {resources} arrived at {target_city.name}")
        
        # Remove completed transfers
        for transfer in completed_transfers:
            self._pending_transfers.remove(transfer)
    
    def get_pending_transfers(self) -> list[dict]:
        """Get list of pending resource transfers."""
        return self._pending_transfers.copy()


class EmptyCity(City):
    """
    Singleton representing a city with no allegiance.
    
    A unit's allegiance to EmptyCity means that the unit has NO allegiance.
    This is a cleaner approach than using None for city references.
    
    Note: Using None is actually simpler. This class is kept for reference only.
    """
    
    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if not hasattr(cls, 'instance'):
            cls.instance = super(EmptyCity, cls).__new__(cls)
        return cls.instance