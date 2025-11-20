"""
Empire: A player-controlled civilization spanning multiple cities.

Empires manage:
- Multiple cities and their resources
- Knowledge and technological advancement
- Autonomy (control vs city independence)
- Ideology and its effects
- Game integration and updates

An empire is the primary unit of player control, with the player acting as
the government making decisions for all allegiant cities.
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from ..systems.government_actions import GovernmentAction

from ..core.constants import HALF_AUTONOMY
from ..core.gameobject import (
    GameObject,
    public_client_property,
    private_client_property,
    HasAllegianceMixin,
)
from ..core.exceptions import BadEffect, CapitalExclusiveException

from ..systems.data import ExpendableEmpireResources, ExpendableCityResources
from ..systems.effects import Effect, EffectWithTicksLeft, UniversalEffect
from ..systems.game_utils import bounded_stat_from_raw, raw_stat_from_bounded

from .ideology import Ideology, NeutralIdeology
from ..gameplay.events import GameEvent

if TYPE_CHECKING:
    from .city import City
    from ..gameplay.game import Game, EmptyGame


class Empire(GameObject, HasAllegianceMixin):
    """
    A player-controlled empire spanning multiple cities.
    
    The empire handles empire-wide mechanics:
    - Multiple cities and their allegiance
    - Knowledge and research
    - Autonomy (how much control cities have independently)
    - Ideology and its effects
    - Communication with the game engine
    
    Key relationships:
    - Every city belongs to exactly one empire (or EmptyEmpire if unclaimed)
    - An empire has one capital city (can be changed)
    - An empire has an ideology affecting all mechanics
    - An empire belongs to one game
    """
    
    def __init__(self, autonomy: int, capital_city: Optional[City], ideology: Ideology):
        """
        Initialize a new empire.
        
        Args:
            autonomy: How much independence cities have (0-100)
            capital_city: The initial capital city (or None)
            ideology: The political ideology of this empire
        """
        super().__init__()
        assert 0 <= autonomy <= 100, f"Autonomy must be 0-100, got {autonomy}"
        
        # Empire resources (knowledge, efficiency, etc.)
        self._empire_resources = ExpendableEmpireResources()

        # Cities controlled by this empire
        self._capital: Optional[City] = capital_city
        self._cities: list[City] = [self._capital] if capital_city is not None else []

        # Knowledge for technological advancement (floating point for precision)
        self._knowledge: float = 50.0
        
        # Raw efficiency (unbounded, 0 = baseline 50 displayed)
        # Efficiency of government actions: when displayed value is 50, actions are normal speed
        # Higher displayed value = faster actions, lower = slower actions
        # Corruption = 100 - efficiency (derived from displayed efficiency)
        self._raw_efficiency: float = 0.0  # Baseline initialization

        #
        self._working_age: int = 18
        self._retirement_age: int = 65

        # How much independent control cities have (0 = micromanage, 100 = full autonomy)
        self._autonomy = autonomy

        # Game engine reference
        self._game: Optional[Game] = None

        # Effects that apply empire-wide or to capital
        self._empire_effects_with_ticks_left: list[EffectWithTicksLeft] = []
        self._ideology: Ideology = ideology
        
        # Game events for tracking important occurrences
        self._game_events: list[GameEvent] = []
        
        # Apply ideology effects (universal and capital-exclusive)
        for ideological_effect in ideology.effects:
            self.add_universal_or_capital_effect(ideological_effect)

    # ========== Properties ==========

    @property
    def allegiance(self) -> Empire:
        """An empire is allegiant to itself."""
        return self

    @public_client_property
    def capital(self) -> Optional[City]:
        """The capital city of this empire."""
        return self._capital

    @private_client_property
    def working_age(self) -> int:
        """The working age of the empire. This is the age people can begin working (but must be trained prior to working)"""
        return self._working_age

    @private_client_property
    def retirement_age(self) -> int:
        """The retirement age of the empire. This is the age people must retire from working"""
        return self._retirement_age
    
    @private_client_property
    def knowledge(self) -> float:
        """Empire-wide knowledge for research and advanced buildings (floating point for precision)."""
        return self._knowledge
    
    @private_client_property
    def efficiency(self) -> float:
        """
        Government efficiency rating (0-100 displayed, higher = faster actions).
        
        This is a computed property derived from the unbounded raw_efficiency value.
        """
        print("raw efficiency", self._raw_efficiency)
        return bounded_stat_from_raw(self._raw_efficiency)
    
    @private_client_property
    def corruption(self) -> float:
        """Government corruption level derived from efficiency (100 - displayed efficiency)."""
        return 100.0 - self.efficiency
    
    @private_client_property
    def autonomy(self) -> int:
        """How much independent control each city has (0-100)."""
        return self._autonomy
    
    @property
    def game(self) -> Optional[Game]:
        """The game engine this empire belongs to."""
        return self._game
    
    @public_client_property
    def current_tick(self) -> Optional[int]:
        """Current game tick from the game engine."""
        if self._game is None:
            return None
        return self._game.current_tick
    
    @private_client_property
    def game_events(self) -> list[GameEvent]:
        """Recent game events tracked for this empire."""
        return self._game_events

    # ========== City Management ==========

    def add_city(self, city: City) -> None:
        """
        Add a city to this empire's control.
        
        Args:
            city: The city to add (will set its allegiance)
        """
        city.set_allegiance(self)
        self._cities.append(city)

    def remove_city(self, city: City) -> None:
        """
        Remove a city from this empire's control (declare independence).
        
        Args:
            city: The city to remove
        """
        city.declare_independence()
        self._cities.remove(city)

    def set_city_as_capital(self, city: City) -> None:
        """
        Change the capital city to a different allegiant city.
        
        Args:
            city: The city to make the new capital
        """
        if city.allegiance is self:
            if self._capital is not None:
                # Remove capital status from current capital
                # (would call city.remove_as_capital() if it exists)
                pass
            
            self._capital = city
            # Set new capital status on city (would call city.set_city_as_capital() if it exists)

    def capture_city(self, city: City) -> None:
        """
        Capture a city that has been conquered.
        
        Called when a city's hitpoints reach 0 from an attack.
        Only captures if city.empire_captured_by is this empire.
        
        Args:
            city: The city to capture
        """
        if city.allegiance is self:
            return  # Already belongs to this empire

        if city.empire_captured_by is None:
            return  # City is not under siege

        if city.empire_captured_by is not self:
            return  # City is being captured by another empire
        
        # Capture the city
        city.set_allegiance(self)
        self.add_city(city)

    # ========== Resources ==========

    def add_knowledge(self, amount: float) -> None:
        """
        Add knowledge to the empire.
        
        Knowledge cannot go below 0. This is the primary method for modifying knowledge;
        it's used by building effects and other game mechanics. Supports floating point
        values for precision when affected by percentage multipliers.
        
        Args:
            amount: The amount of knowledge to add (can be negative, float for precision)
        """
        self._knowledge += float(amount)
        if self._knowledge < 0:
            self._knowledge = 0.0
    
    def add_raw_efficiency(self, amount: float) -> None:
        """
        Add efficiency to the empire by modifying raw efficiency (or subtract to reduce efficiency).
        
        This method modifies the unbounded raw_efficiency value, which is then converted
        to a displayed efficiency (0-100) using a hyperbolic tangent curve. Higher displayed
        efficiency means faster government actions. Corruption is computed as (100 - displayed_efficiency).
        
        This is the primary method for modifying efficiency; it's used by building effects
        and other game mechanics. Effects specify efficiency_per_tick which directly adds to
        raw_efficiency.
        
        Args:
            amount: The amount to add to raw_efficiency (can be negative for corruption effects)
                   Due to the conversion curve, adding/subtracting from raw_efficiency has
                   diminishing returns near the extremes, preventing easy saturation.
        """
        self._raw_efficiency += float(amount)
    
    def add_corruption(self, amount: float) -> None:
        """
        DEPRECATED: Use add_raw_efficiency() instead.
        
        Add corruption to the empire (reduces efficiency).
        Provided for backward compatibility. Reduces efficiency by the given amount.
        
        Args:
            amount: The amount of corruption to add (will reduce efficiency)
        """
        # Corruption = 100 - efficiency, so adding corruption means subtracting efficiency
        self.add_raw_efficiency(-float(amount))

    # ========== Effects ==========

    def add_universal_or_capital_effect(self, effect: Effect) -> None:
        """
        Add an empire-wide or capital-exclusive effect.
        
        Universal effects apply to all cities. Capital-exclusive effects only
        apply when a city is the capital. This is used for ideology effects
        and other empire-wide bonuses/penalties.
        
        Args:
            effect: The effect to add (must be universal or capital-exclusive)
            
        Raises:
            BadEffect: If effect is neither universal nor capital-exclusive
        """
        if not (effect.is_universal() or effect.capital_effect):
            raise BadEffect(
                f"Empire effects must be universal or capital-exclusive, "
                f"got effect with is_universal={effect.is_universal()}, "
                f"capital_effect={effect.capital_effect}"
            )
        
        # Keep reference to empire-level effects
        self._empire_effects_with_ticks_left.append(EffectWithTicksLeft(
            effect=effect,
            ticks_left=effect.duration_in_ticks
        ))

        # Distribute effect to all cities
        # (Cities will only apply capital-exclusive effects if they are the capital)
        for city in self._cities:
            city.add_effect(effect)
    
    # ========== Game Events ==========
    
    def record_event(self, event: GameEvent) -> None:
        """
        Record a significant game event for this empire.
        
        Events are tracked for player information and UI display. Events
        are timestamped automatically and stored in the empire's event log.
        
        Args:
            event: The GameEvent to record
        """
        self._game_events.append(event)
    
    def get_recent_events(self, count: int = 5) -> list[GameEvent]:
        """
        Get the most recent game events.
        
        Args:
            count: Number of recent events to return (default 5)
            
        Returns:
            List of the most recent events (newest first)
        """
        return list(reversed(self._game_events[-count:]))
    
    def clear_events(self) -> None:
        """Clear all recorded game events."""
        self._game_events.clear()

    # ========== Government Actions ==========

    def execute_government_action(self, action: GovernmentAction) -> tuple[bool, str]:
        """
        Execute a government action for this empire.
        
        Government actions cost wealth from the capital city and apply effects
        to one or more cities. The action's can_execute method is checked first.
        
        Args:
            action: The government action to execute
            
        Returns:
            Tuple of (success: bool, message: str)
            
        Raises:
            ImportError: If government_actions module can't be imported
        """
        # Import here to avoid circular dependency
        from ..systems.government_actions import GovernmentAction
        
        if not isinstance(action, GovernmentAction):
            return False, f"Invalid action type: {type(action)}"
        
        # Check if action can execute
        can_execute, reason = action.can_execute(self)
        if not can_execute:
            return False, f"Cannot execute {action.name}: {reason}"
        
        # Deduct cost from capital
        if action.cost_wealth > 0 and self.capital is not None:
            self.capital.expend_city_resources(
                ExpendableCityResources(wealth=action.cost_wealth),
                tag="government_action"
            )
        
        # Get the effect and apply it to capital
        effect = action.get_effect()
        if self.capital is not None:
            if action.name.startswith("Subsidy"):
                # Subsidies apply to a specific city
                # Store the speedup multiplier in the effect
                self.capital.add_effect(effect)
            elif action.name.startswith("Hold Elections"):
                # Elections apply to capital
                self.capital.add_effect(effect)
            else:
                # General effects apply to capital (taxes, propaganda)
                self.capital.add_effect(effect)
        
        print(f"✓ {action.name} executed for {self.capital.name if self.capital else 'unknown city'}")
        return True, f"{action.name} successfully executed"
    
    def get_available_government_actions(self) -> list[str]:
        """
        Get list of government actions available to this empire based on ideology.
        
        Returns:
            List of action names (e.g., ["tax_light", "tax_moderate", "election"])
        """
        from ..systems.government_actions import GovernmentActionRegistry
        
        ideology_name = type(self._ideology).__name__
        return GovernmentActionRegistry.get_available_actions(ideology_name)

    # ========== Game Integration ==========

    def assigned_to_game(self) -> bool:
        """Returns True if this empire is assigned to a game engine."""
        return self._game is not None

    def assign_to_game(self, game: Game) -> None:
        """
        Assign this empire to a game engine.
        
        Only assigns if not already assigned to a game.
        
        Args:
            game: The game engine to assign to
        """
        if not self.assigned_to_game():
            self._game = game

    def update(self, current_tick: int) -> None:
        """
        Process one game tick for this empire.
        
        Updates all cities in the empire.
        
        Args:
            current_tick: The current game tick
        """
        for city in self._cities:
            print("updating city", city)
            city.update()


class EmptyEmpire(Empire):
    """
    Singleton representing no empire (neutral/unclaimed cities).
    
    A city's allegiance to EmptyEmpire means the city has NO allegiance.
    This is cleaner than using None for city.allegiance references.
    
    Note: Using None is actually simpler. This class is kept for reference.
    """
    
    def __new__(cls):
        """Ensure only one instance exists (singleton pattern)."""
        if not hasattr(cls, "instance"):
            cls.instance = super().__new__(cls)
            
            # Create a neutral ideology for the empty empire
            neutral_ideology = NeutralIdeology(effects_list=[])
            
            # Initialize the empire with neutral settings
            # (only called once on first instantiation)
            Empire.__init__(
                cls.instance,
                autonomy=0,
                capital_city=None,
                ideology=neutral_ideology
            )
        return cls.instance
    
    def __init__(self):
        """
        Override __init__ to prevent re-initialization.
        
        Since this is a singleton, we don't want __init__ called multiple times.
        """
        pass