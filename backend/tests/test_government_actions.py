"""
Unit tests for the Government Actions system.

Tests verify that:
- TaxAction correctly applies different intensity levels
- SubsidyAction properly speeds up jobs
- ElectionAction works for Republics only
- PropagandaAction applies correct effects
- Government actions correctly calculate costs and durations
"""

from capstone.backend.systems.government_actions import (
    TaxAction, SubsidyAction, ElectionAction, PropagandaAction,
    GovernmentActionRegistry
)
from capstone.backend.systems.data import ExpendableCityResources
from capstone.backend.systems.effects import Effect
from capstone.backend.core.constants import (
    TAX_INTENSITY_1_MORALE_PENALTY, TAX_INTENSITY_1_WEALTH_GAIN, TAX_INTENSITY_1_DURATION,
    TAX_INTENSITY_2_MORALE_PENALTY, TAX_INTENSITY_2_WEALTH_GAIN, TAX_INTENSITY_2_DURATION,
    TAX_INTENSITY_3_MORALE_PENALTY, TAX_INTENSITY_3_WEALTH_GAIN, TAX_INTENSITY_3_DURATION,
    ELECTION_COST, ELECTION_DURATION, ELECTION_MORALE_BOOST,
    PROPAGANDA_PATRIOTIC_COST, PROPAGANDA_PATRIOTIC_DURATION,
    PROPAGANDA_ECONOMIC_COST, PROPAGANDA_ECONOMIC_DURATION,
    PROPAGANDA_POPULIST_COST, PROPAGANDA_POPULIST_DURATION,
    PROPAGANDA_ENVIRONMENTAL_COST, PROPAGANDA_ENVIRONMENTAL_DURATION,
)


class TestTaxAction:
    """Tests for TaxAction government action."""
    
    def test_tax_intensity_1_parameters(self):
        """Test Tax Level 1 has correct parameters."""
        tax = TaxAction(intensity=1)
        
        assert tax.intensity == 1
        assert tax.name == "Tax Level 1"
        assert tax.wealth_gain == TAX_INTENSITY_1_WEALTH_GAIN
        assert tax.morale_penalty == TAX_INTENSITY_1_MORALE_PENALTY
        assert tax.duration_ticks == TAX_INTENSITY_1_DURATION
        assert tax.cost_wealth == 0  # Taxes have no wealth cost
    
    def test_tax_intensity_2_parameters(self):
        """Test Tax Level 2 has correct parameters."""
        tax = TaxAction(intensity=2)
        
        assert tax.intensity == 2
        assert tax.name == "Tax Level 2"
        assert tax.wealth_gain == TAX_INTENSITY_2_WEALTH_GAIN
        assert tax.morale_penalty == TAX_INTENSITY_2_MORALE_PENALTY
        assert tax.duration_ticks == TAX_INTENSITY_2_DURATION
    
    def test_tax_intensity_3_parameters(self):
        """Test Tax Level 3 has correct parameters."""
        tax = TaxAction(intensity=3)
        
        assert tax.intensity == 3
        assert tax.name == "Tax Level 3"
        assert tax.wealth_gain == TAX_INTENSITY_3_WEALTH_GAIN
        assert tax.morale_penalty == TAX_INTENSITY_3_MORALE_PENALTY
        assert tax.duration_ticks == TAX_INTENSITY_3_DURATION
    
    def test_tax_invalid_intensity(self):
        """Test that invalid intensity raises ValueError."""
        try:
            TaxAction(intensity=0)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
        
        try:
            TaxAction(intensity=4)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
    
    def test_tax_get_effect(self):
        """Test that tax action creates correct effect."""
        tax = TaxAction(intensity=1)
        effect = tax.get_effect()
        
        assert isinstance(effect, Effect)
        assert effect.duration_in_ticks == TAX_INTENSITY_1_DURATION
        assert effect.expendable_city_resources_per_tick.wealth == TAX_INTENSITY_1_WEALTH_GAIN
        assert effect.raw_morale_per_tick == -TAX_INTENSITY_1_MORALE_PENALTY
    
    def test_tax_get_cost(self):
        """Test that tax action returns correct cost."""
        tax = TaxAction(intensity=2)
        cost = tax.get_cost()
        
        assert isinstance(cost, ExpendableCityResources)
        assert cost.wealth == 0  # Taxes are free


class TestSubsidyAction:
    """Tests for SubsidyAction government action."""
    
    def test_subsidy_default_parameters(self):
        """Test SubsidyAction with default parameters."""
        # Mock city object
        class MockCity:
            pass
        
        city = MockCity()
        subsidy = SubsidyAction(target_city=city)
        
        assert subsidy.target_city is city
        assert subsidy.speedup_multiplier == 2.0  # Default from constants
        assert subsidy.cost_wealth == 20  # Default from constants
        assert subsidy.duration_ticks == 5
    
    def test_subsidy_custom_speedup(self):
        """Test SubsidyAction with custom speedup."""
        class MockCity:
            pass
        
        city = MockCity()
        subsidy = SubsidyAction(target_city=city, speedup_multiplier=3.0, cost_wealth=30)
        
        assert subsidy.speedup_multiplier == 3.0
        assert subsidy.cost_wealth == 30
    
    def test_subsidy_invalid_speedup(self):
        """Test that invalid speedup multiplier raises ValueError."""
        class MockCity:
            pass
        
        city = MockCity()
        
        # Too low
        try:
            SubsidyAction(target_city=city, speedup_multiplier=0.2)
            assert False, "Should have raised ValueError for too low speedup"
        except ValueError:
            pass
        
        # Too high
        try:
            SubsidyAction(target_city=city, speedup_multiplier=10.0)
            assert False, "Should have raised ValueError for too high speedup"
        except ValueError:
            pass
    
    def test_subsidy_get_effect(self):
        """Test that subsidy creates correct effect."""
        class MockCity:
            pass
        
        city = MockCity()
        subsidy = SubsidyAction(target_city=city, speedup_multiplier=2.0)
        effect = subsidy.get_effect()
        
        assert isinstance(effect, Effect)
        assert effect.job_speedup_multiplier == 2.0
        assert effect.duration_in_ticks == 5


class TestElectionAction:
    """Tests for ElectionAction government action."""
    
    def test_election_parameters(self):
        """Test ElectionAction has correct parameters."""
        election = ElectionAction()
        
        assert election.name == "Hold Elections"
        assert election.cost_wealth == ELECTION_COST
        assert election.duration_ticks == ELECTION_DURATION
    
    def test_election_get_effect(self):
        """Test that election creates correct effect."""
        election = ElectionAction()
        effect = election.get_effect()
        
        assert isinstance(effect, Effect)
        assert effect.duration_in_ticks == ELECTION_DURATION
        assert effect.raw_morale_per_tick == ELECTION_MORALE_BOOST
    
    def test_election_get_cost(self):
        """Test that election returns correct cost."""
        election = ElectionAction()
        cost = election.get_cost()
        
        assert isinstance(cost, ExpendableCityResources)
        assert cost.wealth == ELECTION_COST


class TestPropagandaAction:
    """Tests for PropagandaAction government action."""
    
    def test_propaganda_patriotic_parameters(self):
        """Test Patriotic Campaign parameters."""
        prop = PropagandaAction("patriotic")
        
        assert prop.campaign_type == "patriotic"
        assert prop.name == "Patriotic Campaign"
        assert prop.cost_wealth == PROPAGANDA_PATRIOTIC_COST
        assert prop.duration_ticks == PROPAGANDA_PATRIOTIC_DURATION
    
    def test_propaganda_economic_parameters(self):
        """Test Economic Stimulus parameters."""
        prop = PropagandaAction("economic")
        
        assert prop.campaign_type == "economic"
        assert prop.name == "Economic Stimulus"
        assert prop.cost_wealth == PROPAGANDA_ECONOMIC_COST
        assert prop.duration_ticks == PROPAGANDA_ECONOMIC_DURATION
    
    def test_propaganda_populist_parameters(self):
        """Test Populist Movement parameters."""
        prop = PropagandaAction("populist")
        
        assert prop.campaign_type == "populist"
        assert prop.name == "Populist Movement"
        assert prop.cost_wealth == PROPAGANDA_POPULIST_COST
        assert prop.duration_ticks == PROPAGANDA_POPULIST_DURATION
    
    def test_propaganda_environmental_parameters(self):
        """Test Environmental Initiative parameters."""
        prop = PropagandaAction("environmental")
        
        assert prop.campaign_type == "environmental"
        assert prop.name == "Environmental Initiative"
        assert prop.cost_wealth == PROPAGANDA_ENVIRONMENTAL_COST
        assert prop.duration_ticks == PROPAGANDA_ENVIRONMENTAL_DURATION
    
    def test_propaganda_invalid_type(self):
        """Test that invalid campaign type raises ValueError."""
        with pytest.raises(ValueError):
            PropagandaAction("invalid_campaign")
    
    def test_propaganda_get_effect_patriotic(self):
        """Test that patriotic campaign creates correct effect."""
        prop = PropagandaAction("patriotic")
        effect = prop.get_effect()
        
        assert isinstance(effect, Effect)
        assert effect.duration_in_ticks == PROPAGANDA_PATRIOTIC_DURATION
        assert effect.expendable_city_resources_per_tick.wealth == 2
        assert effect.raw_morale_per_tick == 2
    
    def test_propaganda_get_effect_economic(self):
        """Test that economic campaign creates correct effect."""
        prop = PropagandaAction("economic")
        effect = prop.get_effect()
        
        assert isinstance(effect, Effect)
        assert effect.duration_in_ticks == PROPAGANDA_ECONOMIC_DURATION
        assert effect.expendable_city_resources_per_tick.wealth == 5
        assert effect.raw_morale_per_tick == -1
    
    def test_propaganda_get_effect_populist(self):
        """Test that populist campaign creates correct effect."""
        prop = PropagandaAction("populist")
        effect = prop.get_effect()
        
        assert isinstance(effect, Effect)
        assert effect.duration_in_ticks == PROPAGANDA_POPULIST_DURATION
        assert effect.raw_morale_per_tick == 3
        # Population increase is stored in new_people_per_tick
        assert effect.new_people_per_tick == 5
    
    def test_propaganda_get_effect_environmental(self):
        """Test that environmental campaign creates correct effect."""
        prop = PropagandaAction("environmental")
        effect = prop.get_effect()
        
        assert isinstance(effect, Effect)
        assert effect.duration_in_ticks == PROPAGANDA_ENVIRONMENTAL_DURATION
        assert effect.expendable_city_resources_per_tick.food == 3
        assert effect.expendable_city_resources_per_tick.timber == 3


class TestGovernmentActionRegistry:
    """Tests for GovernmentActionRegistry."""
    
    def test_registry_universal_actions(self):
        """Test that universal actions are defined."""
        actions = GovernmentActionRegistry.UNIVERSAL_ACTIONS
        
        assert "tax_light" in actions
        assert "tax_moderate" in actions
        assert "tax_heavy" in actions
        assert "propaganda_patriotic" in actions
        assert "propaganda_economic" in actions
        assert "propaganda_populist" in actions
    
    def test_registry_ideology_specific_actions(self):
        """Test that ideology-specific actions are defined."""
        registry = GovernmentActionRegistry.IDEOLOGY_SPECIFIC_ACTIONS
        
        assert "Republic" in registry
        assert "Monarchy" in registry
        assert "Dictatorship" in registry
        assert "election" in registry["Republic"]
    
    def test_registry_create_tax_action(self):
        """Test creating tax actions via registry."""
        action1 = GovernmentActionRegistry.create_action("tax_light")
        action2 = GovernmentActionRegistry.create_action("tax_moderate")
        action3 = GovernmentActionRegistry.create_action("tax_heavy")
        
        assert isinstance(action1, TaxAction)
        assert isinstance(action2, TaxAction)
        assert isinstance(action3, TaxAction)
        assert action1.intensity == 1
        assert action2.intensity == 2
        assert action3.intensity == 3
    
    def test_registry_create_election_action(self):
        """Test creating election action via registry."""
        action = GovernmentActionRegistry.create_action("election")
        
        assert isinstance(action, ElectionAction)
    
    def test_registry_create_propaganda_actions(self):
        """Test creating propaganda actions via registry."""
        patriotic = GovernmentActionRegistry.create_action("propaganda_patriotic")
        economic = GovernmentActionRegistry.create_action("propaganda_economic")
        populist = GovernmentActionRegistry.create_action("propaganda_populist")
        
        assert isinstance(patriotic, PropagandaAction)
        assert isinstance(economic, PropagandaAction)
        assert isinstance(populist, PropagandaAction)
        assert patriotic.campaign_type == "patriotic"
        assert economic.campaign_type == "economic"
        assert populist.campaign_type == "populist"
    
    def test_registry_invalid_action(self):
        """Test that creating invalid action raises ValueError."""
        with pytest.raises(ValueError):
            GovernmentActionRegistry.create_action("invalid_action")
    
    def test_registry_get_available_actions_republic(self):
        """Test getting available actions for Republic ideology."""
        actions = GovernmentActionRegistry.get_available_actions("Republic")
        
        # Should have universal actions + republic-specific
        assert "tax_light" in actions
        assert "propaganda_patriotic" in actions
        assert "election" in actions
    
    def test_registry_get_available_actions_monarchy(self):
        """Test getting available actions for Monarchy ideology."""
        actions = GovernmentActionRegistry.get_available_actions("Monarchy")
        
        # Should have universal actions + monarchy-specific
        assert "tax_light" in actions
        assert "propaganda_patriotic" in actions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])