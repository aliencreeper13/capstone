"""
Ideology system representing different governmental systems.

Each empire chooses an ideology at the start, which affects morale, knowledge generation,
corruption, and other empire-wide mechanics. Ideology cannot be changed mid-game.
"""

from __future__ import annotations

from ..systems.government_actions import ElectionAction, GovernmentAction, PropagandaAction, TaxAction

from ..systems.data import ExpendableCityResources, ExpendableEmpireResources
from ..systems.effects import Effect, UniversalEffect
from ..core.gameobject import GameObject, DataclassGameObject, public_client_property
from ..core.constants import (FOOD_CONSUMPTION_SENSITIVITY, AUTOMATIC_FOOD_CONSUMPTION_EFFECT_ID, 
                              LACK_OF_FOOD_MORALE_PENALTY, MORALE_DEPLETION_DUE_TO_HUNGER_EFFECT_ID)


class Ideology(GameObject):
    """
    Base class for governmental ideologies.
    
    An ideology provides a set of universal effects that apply to all cities
    in an empire. Each ideology has a mix of neutral (universal) and
    ideology-specific effects.
    
    Attributes:
        _neutral_effects: Effects common to all ideologies
        _ideological_specific_effects: Effects specific to this ideology
    """
    
    def __init__(self, effects_list: list[Effect], autonomy: int, government_actions: list[GovernmentAction]):
        """
        Initialize an ideology with its specific effects.
        
        Args:
            effects_list: List of effects this ideology provides
        """
        self._neutral_effects = Ideology.neutral_effects()
        self._ideological_specific_effects = effects_list
        if autonomy < 0 or autonomy > 100:
            raise ValueError("Autonomy must be between 0 and 100")
        self._autonomy = autonomy  # Autonomy level (0-100) for cities under this ideology
        self._government_actions = government_actions


    @public_client_property
    def effects(self) -> list[Effect]:
        """Get all effects (neutral + specific) for this ideology."""
        return self._neutral_effects + self._ideological_specific_effects
    @public_client_property
    def autonomy(self) -> int:
        """Get the autonomy level for cities under this ideology."""
        return self._autonomy
    @public_client_property
    def government_actions(self) -> list[GovernmentAction]:
        """Get the list of government actions available under this ideology."""
        return Ideology.neutral_government_actions() + self._government_actions
    
    @classmethod
    def neutral_effects(cls) -> list[Effect]:
        """
        Get the universal effects all ideologies share.
        Recall that universal effects apply to all cities of an empire.
        
        Returns:
            List of universal effects
        """
        return [UniversalEffect(
            expendable_city_resources_per_tick=ExpendableCityResources(
                food=1,
                timber=1,
                metal=1,
                wealth=1
                
            ),
            theoretical_new_people_per_tick=2,
            theoretical_new_employable_per_tick=1, # it's called "theoretical" because the actual population growth is rounded to an integer 
            # effect_id=273847293847942387238972398478439
        ), # Single effect that scales food consumption with population
        UniversalEffect(
            duration_in_ticks=0,  # indefinite
            contingency_check=lambda city: city._resources.food > 0,
            dynamic_expendable_city_resources_per_tick=lambda c: 
                ExpendableCityResources(food=-(c.total_population * FOOD_CONSUMPTION_SENSITIVITY))
        ),
            UniversalEffect(
            duration_in_ticks=0, # indefinite
            contingency_check=lambda c: c._resources.food <= 0,
            raw_morale_per_tick=-1.0
    )]

    @classmethod
    def neutral_government_actions(cls) -> list[GovernmentAction]:
        """
        Get the default government actions available to all ideologies.
        
        Returns:
            List of default government actions
        """
        # if the ideology is anything other than Anarchy, return TaxAction
        # if the ideology is Anarchy, return empty list
        if cls.__name__ == 'Anarchy':
            return []
        else:
            return [TaxAction()]
class NeutralIdeology(Ideology):
    """
    Neutral ideology with no special effects or penalties.
    
    Only has the baseline universal effects.
    Useful for testing or as a default fallback.
    """
    
    def __init__(self):
        """Initialize neutral ideology with no special effects."""
        super().__init__([], autonomy=50, government_actions=[TaxAction()])  # Neutral autonomy with basic tax action


class Monarchy(Ideology):
    """
    Monarchy ideology: Morale boost but slower knowledge generation.
    
    Effects:
        +1 morale per tick
        -2% knowledge generation
    """
    
    def __init__(self):
        """Initialize monarchy with morale boost and knowledge penalty."""
        super().__init__([
            UniversalEffect(
                duration_in_ticks=0,
                raw_morale_per_tick=1,
                expendable_empire_resources_pct_increase=ExpendableEmpireResources(
                    knowledge=-2
                ),
                raw_efficiency_per_tick=-0.5
            )
        ],
            autonomy=30,
            government_actions=[TaxAction(intensity=3),               # moderate taxation
                PropagandaAction("patriotic")])  # Monarchical cities have lower autonomy


class Republic(Ideology):
    """
    Republic ideology: Citizen happiness and engagement benefits, but risk of revolts.
    
    Effects:
        +0.5 morale per tick (citizen engagement)
        +5% wealth generation (trade and markets)
        Risk of city revolts if morale drops below 20 (handled in city.py)
    """
    
    def __init__(self):
        """Initialize republic with morale and wealth bonuses."""
        super().__init__([
            UniversalEffect(
                duration_in_ticks=0,
                raw_morale_per_tick=0.5,
                expendable_city_resources_pct_increase=ExpendableCityResources(
                    wealth=5
                ),
                raw_efficiency_per_tick=0.5
            )
        ],
        autonomy=50,
        government_actions=[
             ElectionAction(),                     # elections available
            TaxAction(intensity=1),               # light taxes
            PropagandaAction("economic"),         # stimulate trade/wealth
        ])  # Republican cities have moderate autonomy


class Communism(Ideology):
    """
    Communism ideology: Equal resource distribution across cities, but higher corruption.
    
    Effects:
        Resources more equally distributed (implementation in game engine)
        -2 efficiency per tick (bureaucratic overhead increases corruption)
        +3% food production (collective farming)
    """
    
    def __init__(self):
        """Initialize communism with food bonus and efficiency penalty."""
        super().__init__([
            UniversalEffect(
                duration_in_ticks=0,
                expendable_city_resources_pct_increase=ExpendableCityResources(
                    food=3
                )
            ),
            # Efficiency penalty for bureaucratic overhead (reduces efficiency = increases corruption)
            UniversalEffect(
                duration_in_ticks=0,
                raw_efficiency_per_tick=-10.0  # -10 raw efficiency per tick = +10 raw corruption per tick
            )
        ],
        autonomy=20,
        government_actions=[
            PropagandaAction("economic"),         # emphasize economic campaigns
            TaxAction(intensity=3),               # light/common taxation
        ])


class Dictatorship(Ideology):
    """
    Dictatorship ideology: Greater control over cities, but severe morale penalties.
    
    Effects:
        Greater control (lower autonomy) - affects city independence
        -0.5 morale per tick (oppressive rule)
        +10% wealth generation (forced labor)
        Higher revolt risk if morale gets too low
    """
    
    def __init__(self):
        """Initialize dictatorship with wealth bonus and morale penalty."""
        super().__init__([
            UniversalEffect(
                duration_in_ticks=0,
                raw_morale_per_tick=-0.05,
                expendable_city_resources_per_tick=ExpendableCityResources(
                    wealth=2,
                    food=1,
                    timber=1,
                    metal=1
                ),
                # effect_id=289237882987234897243893
            )
        ],
        autonomy=0,
        government_actions=[
             TaxAction(intensity=3),               # heavy taxation
            PropagandaAction("patriotic"),        # state propaganda
        ])  # Dictatorial cities have no autonomy


class Anarchy(Ideology):
    """
    Anarchy ideology: Extreme city autonomy, but high risk of mismanagement.
    
    Effects:
        Cities have extreme independence (autonomy = 80+)
        -5% resource production (lack of coordination)
        +2% population growth (more freedom)
        Risk of cities making poor decisions or revolting
    """
    
    def __init__(self):
        """Initialize anarchy with mixed effects."""
        super().__init__([
            UniversalEffect(
                duration_in_ticks=0,
                expendable_city_resources_pct_increase=ExpendableCityResources(
                    food=-5,
                    timber=-5,
                    metal=-5,
                    wealth=-5
                ),
                new_people_per_tick=5,  # Additional population growth
                raw_efficiency_per_tick=-15, # efficiency penalty to simulate mismanagement
            )
        ],
        autonomy=99,
        government_actions=[])  # Anarchic cities have very high autonomy 
                      # autonomy (can't be 100 because that would make player action impossible)


class Socialism(Ideology):
    """
    Socialism ideology: Higher baseline morale, but reduced wealth generation.
    
    Effects:
        +1.5 morale per tick (social welfare)
        -15% wealth generation (redistributed resources)
        +8% food production (collective planning)
    """
    
    def __init__(self):
        """Initialize socialism with morale and food bonuses, wealth penalty."""
        super().__init__([
            UniversalEffect(
                duration_in_ticks=0,
                raw_morale_per_tick=1.5,
                raw_efficiency_per_tick=-5, # efficiency penalty to simulate bureaucracy
                expendable_city_resources_pct_increase=ExpendableCityResources(
                    food=8,
                    wealth=-15,
                    timber=-5
                )
            )
        ],
        autonomy=25,
        government_actions=[
             PropagandaAction("populist"),         # focus on social programs
            TaxAction(intensity=2),
        ])


class Theocracy(Ideology):
    """
    Theocracy ideology: Religious buildings provide enhanced morale, but slower science.
    
    Effects:
        +1.5 morale per tick (religious devotion)
        -10% knowledge generation (prioritize faith over science)
        +0.5 morale per tick from religious buildings (via building effects)
    """
    
    def __init__(self):
        """Initialize theocracy with morale bonus and knowledge penalty."""
        super().__init__([
            UniversalEffect(
                duration_in_ticks=0,
                raw_morale_per_tick=1.5,
                expendable_empire_resources_pct_increase=ExpendableEmpireResources(
                    knowledge=-10
                )
            )
        ],
        autonomy=30,
        government_actions=[
            PropagandaAction("patriotic"),        # religious/state propaganda
            TaxAction(intensity=2),               # moderate taxation
        ])