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
from random import random

from ..gameplay.events import GameEvent



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
from ..systems.game_utils import new_game_dataclass_given_morale, new_value_given_morale, bounded_stat_from_raw

from .unit import Unit
from .building import Building
from .army import Army, Troop
from .passive import PassiveUnit
from .mobile_unit import MobileUnit

from ..core.exceptions import (
    IllegalMoveException,
    NotAssignedToGameException,
    NotEnoughWorkersException,
    RequirementsException,
)

if TYPE_CHECKING:
    from .empire import Empire
    from ..gameplay.location import GameNode, Path


class City(GameObject, HasAllegianceMixin):
    """
    A city: player-controlled urban center for economy and warfare.
    
    Manages:
    - Resources (food, timber, metal, wealth) and capacities
    - Population (total, employable, employed)
    - Buildings and their effects
    - Job queue (construction, upgrades, unit creation)
    - Mobile unit groups (troops and passive units)
    - Morale, defense, and combat
    - Effects and their ticks remaining
    
    Mobile Unit Groups:
    - Troops (combat units) go into the troop group
    - Passive units go into the passive unit group
    - All movement/location mechanics work identically for both group types
    
    A city is contained within a GameNode and has its own size separate from
    the node's size. The city's size must not exceed its node's size.
    Each city can be allied with an Empire.
    """
    
    def __init__(self, gamenode: GameNode, size: int = 5, morale: float = 50.0):
        """
        Initialize a new city within a game node.
        
        Args:
            gamenode: The GameNode this city is located in
            size: Total space available for buildings (must not exceed node size)
            morale: Initial morale (0-100, default 50)
        """
        super().__init__()
        # print("Gamenode", gamenode)
        if size > gamenode.size:
            raise ValueError(f"City size ({size}) cannot exceed GameNode size ({gamenode.size})")
        
        self._gamenode: GameNode = gamenode
        self._size: int = size

        self.name = "New City"
        
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
            self._raw_morale = 0.0  # Baseline case (where morale=HALF_MORALE)
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

        # MobileUnitGroup for troop production (military units go here)
        self._troop_group: Army = Army(allegiance=None, initial_gamenode=self._gamenode)
        self._gamenode.add_army(self._troop_group)
        
        # MobileUnitGroup for passive unit production (passive units go here)
        self._passive_unit_group: Army = Army(allegiance=None, initial_gamenode=self._gamenode)
        self._gamenode.add_army(self._passive_unit_group)
    
    # ========== Properties ==========

    @property
    def gamenode(self) -> GameNode:
        """The GameNode this city is contained within."""
        from ..gameplay.location import GameNode
        return self._gamenode
    @property
    def coords(self) -> tuple[int, int]:
        return self.gamenode.coords

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
        
        Combines base defense, building effects, and allied armies on the node.
        """
        total_defense = self._base_defense
        
        # Add defense from active effects
        for effect_with_ticks_left in self._effects_with_ticks_left:
            if not effect_with_ticks_left.is_finished():
                total_defense += effect_with_ticks_left.effect.city_base_defense_offered
        
        # Add defense from allied armies stationed on the gamenode
        for army in self._gamenode.armies():
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
        return self._available_space()
    
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
        
        return total_protection
    
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
    def expendable_city_resources(self) -> ExpendableCityResources:
        return self._resources
    
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
        """Population trained to work (employable but not yet employed)."""
        # This is computed from the population's age-based lists
        total_employable = self._societal_resources.employable_population
        total_employed = self._societal_resources.employed_population
        # Unemployable employable = employable - employed
        return total_employable - total_employed
    
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
        """
        Assign this city to an empire.
        
        Updates both the troop group and passive unit group to serve the empire.
        """
        self._allegiance = allegiance
        self._troop_group.set_allegiance(empire=allegiance)
        self._passive_unit_group.set_allegiance(empire=allegiance)

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
            NotEnoughWorkersException: If not enough unemployed employable population
        """
        # Check if there are enough unemployed employable workers
        unemployed = self._societal_resources.employable_population
        if unemployed < num_people:
            raise NotEnoughWorkersException(
                f"Not enough unemployed workers: have {unemployed}, need {num_people}"
            )
        # Use the population's employ_workers method to handle age-based employment
        self._societal_resources.population.employ_workers(num_people)

    def _lay_off_workers(self, num_people: int) -> None:
        """
        Release workers from a completed job.
        
        Args:
            num_people: Number of workers to release
            
        Raises:
            NotEnoughWorkersException: If not enough employed population
        """
        employed = self._societal_resources.employed_population
        if employed < num_people:
            raise NotEnoughWorkersException(
                f"Not enough employed workers to lay off: have {employed}, need {num_people}"
            )
        # Use the population's layoff_workers method to handle age-based layoffs
        self._societal_resources.population.layoff_workers(num_people)

    def increase_population(self, new_people: int) -> None:
        """
        Increase the total population of the city.
        
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
            self._societal_resources.population.add_population(people_to_add)

    # ========== Space and Buildings ==========

    def _available_space(self) -> int:
        """
        Calculate remaining space for new buildings.
        Counts the space contributed by ongoing jobs
        (i.e., buildings under construction still occupy space).
        """
        total_actual_occupied_space: int = 0
        for building in self._buildings:
            total_actual_occupied_space += building.size
        job_occupied_space: int = 0
        for job in self._running_jobs:
            job_occupied_space += job.space_needed

        return self._size - total_actual_occupied_space - job_occupied_space
    
    def _add_building(self, building: Building) -> bool:
        """
        Add a completed building to the city.
        
        When a building is added, its effects are applied, including any max_lifespan_increase
        that is applied immediately to the population (not recalculated each tick).
        
        Args:
            building: The building to add

        Returns: True if successfully added building, False otherwise
        """
        
        # if no space for new building, then end gracefully and create game
        # event that explains the building could not be built
        if self._available_space() <= 0:

            return False

        # assert self._remaining_space() > 0, "No space for new building"
        # assert building not in self._buildings, "Building already in city"
        if building in self._buildings:
            print("WARNING: Building already in city")
            return False 

        self._buildings.append(building)
        # self._size -= building.size
        building.set_city(self)
        building.set_active()
        # Apply building's passive effects
        self.add_effect(effect=building.effect)

        return True

    def _destroy_building(self, building: Building) -> None:
        """
        Destroy a building and reclaim its space.
        
        Args:
            building: The building to destroy
        """
        building.set_inactive()
        self._size += building.size
        self._buildings.remove(building)

    # ========== Army and Units ==========

    def _add_troop(self, troop: Troop) -> None:
        """
        Add a newly created military unit (Troop) to the troop group.
        
        Args:
            troop: The troop to add
        """
        assert not self._troop_group.has_unit(mobile_unit=troop), "Unit already in troop group"
        troop.set_allegiance(empire=self.allegiance)
        self._troop_group.add_troop(troop=troop)
        troop.set_active()
    
    def _add_passive_unit(self, passive_unit: MobileUnit) -> None:
        """
        Add a newly created passive unit to the passive unit group.
        
        Passive units produce resources or provide other non-combat benefits.
        They have 0 damage and follow the same movement/location rules as troops.
        
        Args:
            passive_unit: The passive unit to add
        """
        assert not self._passive_unit_group.has_unit(mobile_unit=passive_unit), "Unit already in passive unit group"
        passive_unit.set_allegiance(empire=self.allegiance)
        self._passive_unit_group.add_mobile_unit(mobile_unit=passive_unit)
        passive_unit.set_active()

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

    def _create_replacement_production_group(self, is_troop: bool) -> Army:
        """
        Create a new empty production group to replace one that has left.
        
        When a production group moves onto a path, a new empty group is created
        so newly created units still have a place to deploy.
        
        Args:
            is_troop: True to create troop group, False for passive unit group
            
        Returns:
            The new empty Army group
        """
        new_group = Army(allegiance=self.allegiance, initial_gamenode=self._gamenode)
        self._gamenode.add_army(new_group)
        return new_group
    
    def move_army_to_path(self, army: Army, path: Path) -> None:
        """
        Move an army from a game node onto a path.
        
        If the army is a production group, automatically creates a replacement.
        
        Args:
            army: The army to move
            path: The path to move the army onto
            
        Raises:
            IllegalMoveException: If army is not in a game node
        """
        from ..gameplay.location import Path
        
        if not army.in_gamenode():
            raise IllegalMoveException("Army must be in a game node to move to a path")
        
        # Check if this is a production group being moved, and replace it
        if army is self._troop_group:
            self._troop_group = self._create_replacement_production_group(is_troop=True)
        elif army is self._passive_unit_group:
            self._passive_unit_group = self._create_replacement_production_group(is_troop=False)
        
        # Move the army onto the path
        army.get_on_path(path)
    
    def halt_army_on_path(self, army: Army) -> bool:
        """
        Halt an army's movement on a path (stops position updates).
        
        This is a marker/state - actual halt logic is handled by game tick system.
        
        Args:
            army: The army to halt
            
        Returns:
            True if halted successfully, False if not on path
        """
        if not army.on_path():
            return False
        
        # Mark army as halted (implementation depends on game tick system)
        # For now, just return success - the game loop can check this
        if not hasattr(army, '_is_halted'):
            army._is_halted = False
        army._is_halted = True
        return True
    
    def resume_army_on_path(self, army: Army) -> bool:
        """
        Resume an army's movement on a path.
        
        Args:
            army: The army to resume
            
        Returns:
            True if resumed successfully, False if not on path
        """
        if not army.on_path():
            return False
        
        if not hasattr(army, '_is_halted'):
            army._is_halted = False
        army._is_halted = False
        return True
    
    def reverse_army_direction(self, army: Army) -> bool:
        """
        Reverse an army's direction on a path.
        
        Reverses the position so the army walks back the way it came.
        
        Args:
            army: The army to reverse
            
        Returns:
            True if reversed successfully, False if not on path
        """
        from ..gameplay.location import Path
        
        if not army.on_path():
            return False
        
        # Get current position on path
        current_path = army._path
        current_position = current_path._armies_and_coords[army]
        
        # Reverse position: if at position X on path of length D,
        # reversed position is D - X
        new_position = current_path.distance - current_position
        current_path._armies_and_coords[army] = new_position
        
        # Mark direction as reversed
        if not hasattr(army, '_direction_reversed'):
            army._direction_reversed = False
        army._direction_reversed = not army._direction_reversed
        
        return True
    
    def get_stationary_armies(self) -> list[Army]:
        """
        Get all armies currently stationed at game nodes.
        
        Returns:
            List of armies at nodes (including production groups)
        """
        stationary = []
        for army in self._gamenode.armies():
            if army.in_gamenode():
                stationary.append(army)
        return stationary
    
    def get_moving_armies(self) -> list[Army]:
        """
        Get all armies currently moving on paths.
        
        Returns:
            List of armies on paths
        """
        from ..gameplay.location import Path
        
        moving = []
        for army in self._gamenode.armies():
            if army.on_path():
                moving.append(army)
        return moving

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
        self._apply_resource_delta(city_resources*-1, clamp_to_capacity=False)

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
            print("Effect failed to apply")
            return

        # Apply resource changes (using dynamic values if available)
        # resource changes are affected by morale
        self.change_resources(
            new_game_dataclass_given_morale(effect.get_baseline_city_resources_per_tick(city=self) * ticks_elapsed * self.expendable_city_resource_factor, self.morale)
        )

        # Apply empire resource changes (including knowledge)
        self.change_empire_resources(effect.get_empire_resources_per_tick(city=self) * ticks_elapsed)
        
        # Apply morale changes
        self.add_raw_morale(effect.get_raw_morale_per_tick(city=self) * ticks_elapsed)
        # self.morale += effect.get_raw_morale_per_tick(city=self) * ticks_elapsed
        
        # Apply efficiency changes (if allegiant to an empire)
        raw_efficiency_per_tick = effect.get_raw_efficiency_per_tick(city=self)
        if raw_efficiency_per_tick != 0.0 and self.allegiance is not None:
            # print("raw efficiency per tick", raw_efficiency_per_tick)
            # print("raw efficiency added:", raw_efficiency_per_tick * ticks_elapsed)
            self.allegiance.add_raw_efficiency(raw_efficiency_per_tick * ticks_elapsed)

        # Apply population growth from effects
        new_people = effect.actual_new_people_per_tick(city=self) * ticks_elapsed
        # if new_people > 0:
        # self._societal_resources.population.add_population(new_people)
        self.increase_population(new_people)
        
        # Apply population loss from effects
        # dead_people = effect.get_dead_people_per_tick(city=self) * ticks_elapsed
        # if dead_people > 0:
            # self._societal_resources.population.remove_population(dead_people)

        # Add new employable people from effect
        new_employable = effect.actual_new_employable_per_tick(city=self) * ticks_elapsed
        # if new_employable > 0:
        self._societal_resources.population.add_employable(new_employable)

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
    def check_job_requirements(self, job: Job) -> tuple[bool, list[str]]:
        """
        Check all job requirements and collect any failures.
        
        Returns:
            Tuple of (all_met: bool, failures: list[str])
        """
        requirements: JobRequirements = job.requirements
        level = job.level_upon_completion
        failures: list[str] = []

        # First, if job is an upgrade or destruction job, check to see if there is
        # already an ongoing job for this unit
        if job.is_upgrade or job.is_destruction:
            for ongoing_job in self._running_jobs:
                if ongoing_job.current_unit is job.current_unit:
                    print("Another job is already ongoing for target unit")
                    failures.append(f"Another job is already ongoing for target unit {job.current_unit.name}")
                    
        

        # Second, check if there's enough space in city if it's a building creation job
        if job.is_creation and issubclass(job.result_class, Building):
            if self._available_space() < job.space_needed:
                failures.append(f"Not enough available city space for job (need {job.space_needed}, have {self._available_space()})")

        # Check specific units are active
        specific_units_contingent_on = requirements.specific_units_contingent_on
        for unit_ in specific_units_contingent_on:
            if not unit_.is_active():
                failures.append(f"Required unit {unit_.name} is not active")

        
            
        # Check unit types are available
        # TODO: Test recent implementation of creation jobs instantiating units
        # at levels higher than 1
        for contingent_on_info in requirements.unit_types_contingent_on:
            if job.is_creation and level > 1:
            # For creation jobs which instantiate their results at a level
            # higher than 1, the minimum level needed for dependent unit classes
            # is higher
                minimum_level_needed = contingent_on_info.minimum_level_needed + level - 1
            else:
                minimum_level_needed = contingent_on_info.minimum_level_needed
            num_satisfying_units = self.units_of_subclass_active_in_city(
                unit_class=contingent_on_info.unit_class,
                minimum_level=minimum_level_needed
            )
            if num_satisfying_units <= 0:
                failures.append(f"Need {contingent_on_info.unit_class.__name__} units (level {minimum_level_needed}+)")

        # Enforce maximum units of this type per city (runs for all jobs, not just those with contingencies)
        if job.is_creation:
            if job.requirements.max_per_city is not None:
                num_units_of_same_subclass_as_result_class = self.units_of_subclass_active_in_city(
                    unit_class=job.result_class,
                    minimum_level=1
                )
                if num_units_of_same_subclass_as_result_class >= job.requirements.max_per_city:
                    failures.append(f"Cannot have more than {job.requirements.max_per_city} units of type {job.result_class.__name__} in city")

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
    def add_job(self, job: Job, from_ai: bool = False) -> tuple[bool, str, list[str]]:
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
        
        

        # Check all requirements
        requirements_met, failures = self.check_job_requirements(job)

        if job.is_creation:
            job_action = "create"
        elif job.is_upgrade:
            job_action = "upgrade"
        elif job.is_destruction:
            job_action = "destroy"
        else:
            job_action = "Submit"
        source = "[PLAYER]"
        if from_ai:
            source = "[AI]"
        job_name = f"{source} {job_action} {job.result_class.name}"
        # Record game event
        if self.allegiance is not None:
            job__result_name = job.result_class.name
            
            if requirements_met:
                # Add job successfully
                level = job.level_upon_completion
                self.expend_city_resources(job.requirements.city_resources(level=level))
                self._employ_people(job.requirements.workers_needed(level=level))
                self._running_jobs.append(job)

                
                
                event = GameEvent(
                    type="job_submission",
                    unix_timestamp=int(datetime.now().timestamp()),
                    source="City",
                    description=f"Job started in {self.name}: {job_name}",
                    data={"city_name": self.name, "job_type": job_name, "status": "started"},
                    triggered_by_ai=from_ai
                )
                message = f"✓ Started job: {job_name}"
            else:
                # Job failed due to missing requirements
                event = GameEvent(
                    type="custom",
                    unix_timestamp=int(datetime.now().timestamp()),
                    source="City",
                    description=f"Job submission failed in {self.name}: {', '.join(failures)}",
                    data={
                        "city_name": self.name,
                        "job_type": job_name,
                        "status": "failed",
                        "reasons": failures
                    },
                    triggered_by_ai=from_ai
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

    def expand_city(self, size_increase: int = 1) -> tuple[bool, str]:
        """
        Expand the city's size (space for buildings).
        
        Costs 500 wealth per size increase. City size cannot exceed gamenode size.
        
        Args:
            size_increase: Number of size units to add (default 1)
            
        Returns:
            Tuple of (success: bool, reason: str)
            - success: True if expansion succeeded, False otherwise
            - reason: Description of result or failure reason
        """
        from ..gameplay.events import GameEvent
        
        wealth_cost = 500 * size_increase
        new_size = self._size + size_increase
        
        failures = []
        
        if self.get_wealth() < wealth_cost:
            failures.append(f"Not enough wealth (need {wealth_cost}, have {self.get_wealth():.0f})")
        
        if new_size > self._gamenode.size:
            failures.append(f"Cannot expand beyond region capacity ({new_size} > {self._gamenode.size})")
        
        if failures:
            reason = ", ".join(failures)
            if self.allegiance is not None:
                event = GameEvent(
                    type="custom",
                    unix_timestamp=int(datetime.now().timestamp()),
                    source="City",
                    description=f"City expansion failed in {self.name}: {reason}",
                    data={
                        "city_name": self.name,
                        "action": "expand_city",
                        "status": "failed",
                        "reasons": failures,
                        "size_attempted": size_increase,
                        "cost": wealth_cost
                    }
                )
                self.allegiance.record_event(event)
            return False, reason
        
        self.expend_city_resources(ExpendableCityResources(wealth=wealth_cost))
        self._size = new_size
        
        reason = f"City expanded to size {self._size}"
        if self.allegiance is not None:
            event = GameEvent(
                type="custom",
                unix_timestamp=int(datetime.now().timestamp()),
                source="City",
                description=f"City expansion succeeded in {self.name}: expanded to size {self._size}",
                data={
                    "city_name": self.name,
                    "action": "expand_city",
                    "status": "success",
                    "new_size": self._size,
                    "cost": wealth_cost
                }
            )
            self.allegiance.record_event(event)
        
        return True, reason

    def _AI_add_random_job(self, can_submit_destruction_jobs: bool = False) -> None:
        """
        AI adds a random job, if there are enough requirements, to the city.
        AI can submit creation jobs, upgrade jobs, and destruction jobs if allowed.
        If no such job can be added, the function returns without adding anything.
        For now, can only add one job per call.
        For now, can only add BUILDING jobs.
        Args: 
            can_submit_destruction_jobs: If True, AI can submit destruction jobs.
        """
        from ..systems.job import CreationJob, UpgradeJob, DestructionJob
        from ..unit_classes import buildings
        import inspect
        
        job_type_attempts = []
        
        if can_submit_destruction_jobs:
            weights = [48, 48, 4]
            job_types = ['creation', 'upgrade', 'destruction']
        else:
            weights = [50, 50]
            job_types = ['creation', 'upgrade']
        
        total_weight = sum(weights)
        rand = random() * total_weight
        cumulative = 0
        primary_job_type = None
        
        for job_type, weight in zip(job_types, weights):
            cumulative += weight
            if rand < cumulative:
                primary_job_type = job_type
                break
        
        job_type_attempts.append(primary_job_type)
        
        for job_type in job_types:
            if job_type != primary_job_type:
                job_type_attempts.append(job_type)
        
        for job_type in job_type_attempts:
            if job_type == 'creation':
                if self._try_add_creation_job(buildings):
                    return
            
            elif job_type == 'upgrade':
                if self._try_add_upgrade_job():
                    return
            
            elif job_type == 'destruction':
                if self._try_add_destruction_job():
                    return
    
    def _try_add_creation_job(self, buildings_module) -> bool:
        """
        Try to add a creation job for a random building class.
        Returns True if a job was successfully added, False otherwise.
        """
        from random import shuffle
        from ..systems.job import CreationJob
        import inspect
        
        building_classes = [
            cls for name, cls in inspect.getmembers(buildings_module, inspect.isclass)
            if issubclass(cls, buildings_module.Building) and cls is not buildings_module.Building
        ]
        
        shuffle(building_classes)
        
        for building_class in building_classes:
            job = CreationJob(building_class, triggered_by_ai=True)
            requirements_met, failures = self.check_job_requirements(job)
            
            if requirements_met:
                success, message, _ = self.add_job(job, from_ai=True)
                return success
        
        return False
    
    def _try_add_upgrade_job(self) -> bool:
        """
        Try to add an upgrade job for a random instantiated building.
        Returns True if a job was successfully added, False otherwise.
        """
        from random import shuffle
        from ..systems.job import UpgradeJob
        
        if not self._buildings:
            return False
        
        shuffled_buildings = self._buildings.copy()
        shuffle(shuffled_buildings)
        
        for building in shuffled_buildings:
            job = UpgradeJob(building, triggered_by_ai=True)
            requirements_met, failures = self.check_job_requirements(job)
            
            if requirements_met:
                success, message, _ = self.add_job(job, from_ai=True)
                return success
        
        return False
    
    def _try_add_destruction_job(self) -> bool:
        """
        Try to add a destruction job for a random instantiated building.
        Returns True if a job was successfully added, False otherwise.
        """
        from random import shuffle
        from ..systems.job import DestructionJob
        
        if not self._buildings:
            return False
        
        shuffled_buildings = self._buildings.copy()
        shuffle(shuffled_buildings)
        
        for building in shuffled_buildings:
            job = DestructionJob(building, triggered_by_ai=True)
            requirements_met, failures = self.check_job_requirements(job)
            
            if requirements_met:
                success, message, _ = self.add_job(job, from_ai=True)
                return success
        
        return False

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
        
        # ===== POPULATION DYNAMICS =====
        # Use the new population dynamics system for comprehensive population changes
        from ..systems.population_dynamics import PopulationDynamics
        
        # Calculate all population changes
        # population_changes = PopulationDynamics.calculate_population_change(self)
        
        # Apply the changes
        # PopulationDynamics.apply_population_changes(self, population_changes)
        
        # Print population report (can be disabled in production)
        # if (population_changes['births'] > 0 or population_changes['net_change'] != 0 or
            # population_changes['deaths_old_age'] > 0 or population_changes['emigration'] > 0):
            # PopulationDynamics.print_population_report(self, population_changes)


        # if production army and/or production passive group has moved out of
        # city's gamenode, then replace production army and/or production passive
        # group with new groups
        if self._troop_group not in self._gamenode.armies():
            self._troop_group = self._create_replacement_production_group(is_troop=True)
        if self._passive_unit_group not in self._gamenode.armies():
            self._passive_unit_group = self._create_replacement_production_group(is_troop=False)    

        # FIXME: This doesn't seem to be working...
        if self._societal_resources.population.employable_population >= self._societal_resources.population.total():
            self._societal_resources.population.employable_population = self._societal_resources.population.total()
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
                        from ..gameplay.events import GameEvent
                        success = self._add_building(job_result)
                        
                        job_name = job_result.__name__ if hasattr(job_result, '__name__') else str(job_result)
                        # TODO: Add refund for failed building jobs
                        if not success:
                            event = GameEvent(
                                type="building_failed",
                                unix_timestamp=int(datetime.now().timestamp()),
                                source="City",
                                description=f"Failed to build {job_result.name} in {self.name}. Insufficient space.",
                                data={"city_name": self.name, "building_type": job_result.name, "status": "failed"},
                                triggered_by_ai=job.triggered_by_ai
                            )
                            message = f"✗ Failed to complete job: {job_name} (insufficient space)"
                        else:
                            
                            event = GameEvent(
                                type="building_completed",
                                unix_timestamp=int(datetime.now().timestamp()),
                                source="City",
                                description=f"Building completed in {self.name}: {job_result.name}",
                                data={"city_name": self.name, "building_type": job_result.name, "status": "completed"},
                                triggered_by_ai=job.triggered_by_ai
                            
                        )
                        message = f"✓ Completed job: {job_name}"
                        self.allegiance.record_event(event)
                        # TODO: Add refund logic if success=False
                elif isinstance(job_result, Troop):
                    assert job_result is not None
                    self._add_troop(job_result)
                    from ..gameplay.events import GameEvent
                    unit_name = getattr(job_result, "name", getattr(job_result, "__name__", str(job_result)))
                    event = GameEvent(
                        type="troop_created",
                        unix_timestamp=int(datetime.now().timestamp()),
                        source="City",
                        description=f"Troop created in {self.name}: {unit_name}",
                        data={"city_name": self.name, "unit_type": unit_name, "status": "created"},
                        triggered_by_ai=job.triggered_by_ai
                    )
                    if self.allegiance is not None:
                        self.allegiance.record_event(event)
                elif isinstance(job_result, PassiveUnit):
                    assert job_result is not None
                    self._add_passive_unit(job_result)
                    from ..gameplay.events import GameEvent
                    unit_name = getattr(job_result, "name", getattr(job_result, "__name__", str(job_result)))
                    event = GameEvent(
                        type="passive_unit_created",
                        unix_timestamp=int(datetime.now().timestamp()),
                        source="City",
                        description=f"Passive unit created in {self.name}: {unit_name}",
                        data={"city_name": self.name, "unit_type": unit_name, "status": "created"},
                        triggered_by_ai=job.triggered_by_ai
                    )
                    if self.allegiance is not None:
                        self.allegiance.record_event(event)
                print("Finished job!")
                self._running_jobs.remove(job)

                # **BUG FIX**: Use job.level_upon_completion instead of job_result.level
                # (job_result doesn't have a level attribute; we use the job's level)
                self._lay_off_workers(job.requirements.workers_needed(level=job.level_upon_completion))
                
                print("Buildings:", self._buildings)

        # ===== AI JOB ADDITION =====
        if self.allegiance is not None and self.autonomy is not None:
            from ..systems.game_utils import probability_ai_adds_job
            
            prob = probability_ai_adds_job(self.autonomy)
            print("AUTONOMY:", self.autonomy)
            # prob = 0 # TEMPORARY
            if random() < prob:
                can_destroy = False
                self._AI_add_random_job(can_submit_destruction_jobs=can_destroy)

        # ===== RESOURCE CONSUMPTION & EFFECTS =====
        # TODO: Make this a single effect with indefinite duration with dynamic raw morale per tick
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
        if self.morale <= MORALE_REVOLT_THRESHOLD:
            print("Revolt should occur...")
        if self._revolt_countdown is not None and self._revolt_countdown > 0:
            print(f"{self.name} REVOLT COUNTDOWN: {self._revolt_countdown} TICKS REMAINING")
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
        
        old_empire_name = self.allegiance.name if hasattr(self.allegiance, 'name') else 'their empire'
        print(f"✗ REVOLT: {self.name} has revolted against {old_empire_name}!")
        self.allegiance.record_event(GameEvent(
                type='city_revolt',
                unix_timestamp=int(datetime.now().timestamp()),
                source='City',
                description=f'{self.name} has revolted against their empire!',
                data={'city_name': self.name},
                triggered_by_ai=False
            ))
        # self.declare_independence()
        # Determine new empire: try previous allegiance, else create AI empire
        if self._previous_allegiance is not None:
            new_empire = self._previous_allegiance
            new_empire_name = new_empire.name if hasattr(new_empire, 'name') else 'the previous empire'
            print(f"  → {self.name} rejoins {new_empire_name}")
            self.allegiance.remove_city(self)
            self._allegiance = new_empire
            new_empire.add_city(self)

        else:
            # Create new AI empire
            from .ideology import NeutralIdeology
            from ..entities.empire import Empire
            new_empire = Empire(autonomy=50, capital_city=self, ideology=NeutralIdeology())
            new_empire.assign_to_game(self.allegiance.game)
            print(f"  → {self.name} becomes capital of new AI empire")
            new_empire.add_city(self)
            self.allegiance.remove_city(self)
            self._allegiance = new_empire
            new_empire.assign_to_game(self.allegiance.game)
            
        
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
        
        dx = abs(self.coords[0] - target_city.gamenode.coords[0])
        dy = abs(self.coords[1] - target_city.gamenode.coords[1])
        distance = max(dx, dy)
        
        # Calculate costs
        wealth_cost = distance * RESOURCE_TRANSFER_WEALTH_COST_PER_TILE
        transfer_ticks = max(1, int(distance * RESOURCE_TRANSFER_TICKS_PER_TILE))
        # transfer_ticks = 4
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
            print(f"Transfer to {transfer['target_city'].name}: {transfer['ticks_remaining']} ticks remaining")
            
            if transfer['ticks_remaining'] <= 0:
                # Transfer complete - add resources to target city
                target_city: City = transfer['target_city']
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