"""
Population Dynamics System: Modeling population growth, decline, and migration.

This system handles:
- Population growth based on food, morale, housing
- Population decline from starvation, disease, war
- Population emigration due to low morale
- Population aging and natural deaths
- Birth rate modifiers from various factors

Population changes are influenced by:
- Food availability (starvation if not enough)
- Morale (high morale = growth, low morale = emigration)
- Housing capacity (can't grow beyond capacity)
- Healthcare (hospitals increase lifespan)
- War/casualties (armies and combat losses)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.city import City


class PopulationDynamics:
    """
    Calculates population changes for a city each tick.
    
    Handles births, deaths, emigration, and population aging.
    """
    
    # Population growth rates (per capita per tick)
    BASE_GROWTH_RATE = 0.01  # 1% growth per tick with ideal conditions
    GROWTH_MORALE_THRESHOLD = 50  # Morale above this encourages growth
    GROWTH_MORALE_BONUS = 0.002  # Additional growth per morale point above threshold
    GROWTH_MORALE_PENALTY = 0.001  # Population loss per morale point below threshold
    
    # Starvation
    STARVATION_DEATH_RATE = 0.05  # 5% of population dies if no food
    
    # Emigration (population leaving due to low morale)
    EMIGRATION_MORALE_THRESHOLD = 20  # People leave if morale below this
    EMIGRATION_BASE_RATE = 0.005  # 0.5% emigration per tick at zero morale
    EMIGRATION_MORALE_FACTOR = 0.0001  # Emigration rate per morale point below threshold
    
    # Natural death from disease/old age (independent of lifespan)
    NATURAL_DEATH_RATE = 0.002  # 0.2% natural death rate per tick
    
    @staticmethod
    def calculate_population_change(city: City) -> dict:
        """
        Calculate population changes for a city this tick.
        
        NOTE: This system assumes age_population() has ALREADY been called by the city.
        This handles births, starvation/natural deaths, and emigration, but NOT aging.
        
        Returns a breakdown of births, deaths, emigration, etc.
        
        Args:
            city: The city to calculate changes for
            
        Returns:
            Dictionary with:
                'births': number of new people born
                'deaths_starvation': number died from starvation
                'deaths_natural': number died from disease
                'emigration': number emigrated
                'net_change': total population change (births - deaths - emigration)
        """
        result = {
            'births': 0,
            'deaths_starvation': 0,
            'deaths_natural': 0,
            'deaths_old_age': 0,  # Already handled by age_population()
            'emigration': 0,
            'net_change': 0,
        }
        
        # Calculate deaths from starvation
        deaths_starvation = PopulationDynamics._calculate_deaths_from_starvation(city)
        result['deaths_starvation'] = deaths_starvation
        
        # Calculate natural deaths from disease
        deaths_natural = PopulationDynamics._calculate_natural_deaths(city)
        result['deaths_natural'] = deaths_natural
        
        # Calculate emigration
        emigration = PopulationDynamics._calculate_emigration(city)
        result['emigration'] = emigration
        
        # Calculate births (only if not starving and have capacity)
        if city.get_food() > 0 and city.total_population < city.population_limit:
            births = PopulationDynamics._calculate_births(city)
            result['births'] = births
        
        # Calculate net change
        total_deaths = deaths_starvation + deaths_natural
        result['net_change'] = result['births'] - total_deaths - emigration
        
        return result
    
    @staticmethod
    def _calculate_deaths_from_starvation(city: City) -> int:
        """Calculate deaths if food is insufficient."""
        if city._resources.food <= 0:
            # Apply starvation death rate
            death_count = int(city.total_population * PopulationDynamics.STARVATION_DEATH_RATE)
            return max(0, death_count)
        return 0
    
    @staticmethod
    def _calculate_natural_deaths(city: City) -> int:
        """Calculate deaths from disease and natural causes."""
        death_count = int(city.total_population * PopulationDynamics.NATURAL_DEATH_RATE)
        return max(0, death_count)
    
    @staticmethod
    def _calculate_emigration(city: City) -> int:
        """Calculate population emigration due to low morale."""
        morale = city.morale
        
        if morale < PopulationDynamics.EMIGRATION_MORALE_THRESHOLD:
            # Calculate emigration rate
            morale_deficit = PopulationDynamics.EMIGRATION_MORALE_THRESHOLD - morale
            emigration_rate = (
                PopulationDynamics.EMIGRATION_BASE_RATE +
                (morale_deficit * PopulationDynamics.EMIGRATION_MORALE_FACTOR)
            )
            
            # Clamp emigration rate
            emigration_rate = min(emigration_rate, 0.2)  # Max 20% emigration per tick
            
            emigration = int(city.total_population * emigration_rate)
            return max(0, emigration)
        
        return 0
    
    @staticmethod
    def _calculate_births(city: City) -> int:
        """Calculate births based on morale, housing, and food."""
        population = city.total_population
        morale = city.morale
        
        # Base growth rate
        growth_rate = PopulationDynamics.BASE_GROWTH_RATE
        
        # Morale modifier
        if morale >= PopulationDynamics.GROWTH_MORALE_THRESHOLD:
            # Bonus growth from good morale
            morale_bonus = (
                (morale - PopulationDynamics.GROWTH_MORALE_THRESHOLD) *
                PopulationDynamics.GROWTH_MORALE_BONUS
            )
            growth_rate += morale_bonus
        else:
            # Penalty from low morale
            morale_penalty = (
                (PopulationDynamics.GROWTH_MORALE_THRESHOLD - morale) *
                PopulationDynamics.GROWTH_MORALE_PENALTY
            )
            growth_rate -= morale_penalty
        
        # Clamp growth rate
        growth_rate = max(growth_rate, -0.05)  # Max 5% decline
        growth_rate = min(growth_rate, 0.05)   # Max 5% growth
        
        # Calculate births
        births = int(population * growth_rate)
        
        # Apply housing capacity limit
        if births > 0:
            available_capacity = city.population_limit - population
            births = min(births, available_capacity)
        
        return max(0, births)
    
    @staticmethod
    def apply_population_changes(city: City, changes: dict) -> None:
        """
        Apply calculated population changes to a city.
        
        NOTE: Does NOT apply aging deaths - those are handled by city.get_population_data().age_population()
        
        Args:
            city: The city to apply changes to
            changes: Dictionary from calculate_population_change()
        """
        population = city.get_population_data()
        
        # Apply starvation deaths (removes from youngest ages first)
        if changes['deaths_starvation'] > 0:
            removed = 0
            for age in range(len(population.population_by_age)):
                if removed >= changes['deaths_starvation']:
                    break
                can_remove = min(
                    population.population_by_age[age],
                    changes['deaths_starvation'] - removed
                )
                population.population_by_age[age] -= can_remove
                removed += can_remove
        
        # Apply natural deaths (distributed proportionally across all ages)
        if changes['deaths_natural'] > 0:
            removed = 0
            for age in range(len(population.population_by_age)):
                if removed >= changes['deaths_natural']:
                    break
                # Remove up to 5% from each age group (more conservative than before)
                can_remove = min(
                    int(population.population_by_age[age] * 0.05),
                    changes['deaths_natural'] - removed
                )
                population.population_by_age[age] -= can_remove
                removed += can_remove
        
        # Apply emigration (mostly working-age population emigrates)
        if changes['emigration'] > 0:
            removed = 0
            for age in range(15, 80):  # Mostly working-age population (15-80) emigrates
                if removed >= changes['emigration']:
                    break
                # Remove up to 10% from each age group (more conservative than 20%)
                can_remove = min(
                    int(population.population_by_age[age] * 0.10),
                    changes['emigration'] - removed
                )
                population.population_by_age[age] -= can_remove
                removed += can_remove
        
        # Apply births
        if changes['births'] > 0:
            population.add_population(changes['births'], age_group=0)
    
    @staticmethod
    def print_population_report(city: City, changes: dict) -> None:
        """
        Print a readable report of population changes.
        
        Args:
            city: The city (for name)
            changes: Dictionary from calculate_population_change()
        """
        total_deaths = (
            changes['deaths_old_age'] +
            changes['deaths_starvation'] +
            changes['deaths_natural']
        )
        net = changes['net_change']
        
        report = f"{city.name} Population: "
        
        if changes['births'] > 0:
            report += f"+{changes['births']} births, "
        
        if total_deaths > 0:
            report += f"-{total_deaths} deaths ("
            if changes['deaths_old_age'] > 0:
                report += f"{changes['deaths_old_age']} old age, "
            if changes['deaths_starvation'] > 0:
                report += f"{changes['deaths_starvation']} starvation, "
            if changes['deaths_natural'] > 0:
                report += f"{changes['deaths_natural']} natural"
            report += "), "
        
        if changes['emigration'] > 0:
            report += f"-{changes['emigration']} emigrated, "
        
        report += f"net: {net:+d} (now {city.total_population})"
        
        print(report)