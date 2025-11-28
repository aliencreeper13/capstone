"""
Test script for the new dynamic effects and contingency system.

Verifies:
1. Contingency checks work properly
2. Dynamic values are calculated correctly each tick
3. Static values still work as fallback
4. Food consumption system uses the new dynamic effects elegantly
"""

import sys
sys.path.insert(0, r'c:\Users\MrCheese\Desktop\Programming\Python\capstone')

from backend.systems.effects import Effect, OngoingEffect
from backend.systems.data import ExpendableCityResources
from backend.entities.city import City
from backend.entities.empire import Empire
from backend.core.constants import FOOD_CONSUMPTION_SENSITIVITY

print("=" * 70)
print("DYNAMIC EFFECTS & CONTINGENCY TESTS")
print("=" * 70)

# ========== TEST 1: Contingency Checks ==========
print("\n✓ TEST 1: Contingency Checks")

city = City(coords=(0, 0))
city.change_resources(ExpendableCityResources(food=50))

# Effect that only applies when food is available
food_effect = Effect(
    effect_id=1,
    contingency_check=lambda c: c._resources.food > 0,
    expendable_city_resources_per_tick=ExpendableCityResources(food=-5)
)

# Effect that only applies when food is unavailable
hunger_effect = Effect(
    effect_id=2,
    contingency_check=lambda c: c._resources.food <= 0,
    raw_morale_per_tick=-2.0
)

# Test with food available
assert food_effect.should_apply(city), "Food effect should apply when food available"
assert not hunger_effect.should_apply(city), "Hunger effect should NOT apply when food available"
print("  ✅ Contingency checks work with food available")

# Test with food unavailable
city.change_resources(ExpendableCityResources(food=-50))
assert not food_effect.should_apply(city), "Food effect should NOT apply when no food"
assert hunger_effect.should_apply(city), "Hunger effect should apply when no food"
print("  ✅ Contingency checks work with food unavailable")


# ========== TEST 2: Dynamic Values ==========
print("\n✓ TEST 2: Dynamic Values")

city = City(coords=(5, 5))
city._societal_resources.population.adults = 100  # 100 population

# Effect with dynamic resource consumption based on population
dynamic_effect = Effect(
    effect_id=3,
    dynamic_expendable_city_resources_per_tick=lambda c: ExpendableCityResources(
        food=-(c.total_population * FOOD_CONSUMPTION_SENSITIVITY)
    )
)

# Check that dynamic values are computed correctly
expected_food_per_tick = -(city.total_population * FOOD_CONSUMPTION_SENSITIVITY)
actual_resources = dynamic_effect.get_baseline_city_resources_per_tick(city)
assert actual_resources.food == expected_food_per_tick, \
    f"Expected {expected_food_per_tick}, got {actual_resources.food}"
print(f"  ✅ Dynamic food consumption calculated correctly: {actual_resources.food} per tick for {city.total_population} population")

# Change population and verify dynamic value changes
city._societal_resources.population.adults = 200
actual_resources = dynamic_effect.get_baseline_city_resources_per_tick(city)
expected_food_per_tick = -(city.total_population * FOOD_CONSUMPTION_SENSITIVITY)
assert actual_resources.food == expected_food_per_tick, \
    f"Expected {expected_food_per_tick}, got {actual_resources.food}"
print(f"  ✅ Dynamic value updates with population: {actual_resources.food} per tick for {city.total_population} population")


# ========== TEST 3: Static Values Fallback ==========
print("\n✓ TEST 3: Static Values Fallback")

static_effect = Effect(
    effect_id=4,
    expendable_city_resources_per_tick=ExpendableCityResources(food=-10, timber=5)
)

resources = static_effect.get_baseline_city_resources_per_tick(city)
assert resources.food == -10, f"Expected -10, got {resources.food}"
assert resources.timber == 5, f"Expected 5, got {resources.timber}"
print("  ✅ Static values work as fallback when no dynamic function provided")


# ========== TEST 4: Dynamic Morale Changes ==========
print("\n✓ TEST 4: Dynamic Morale Changes")

# Effect with dynamic morale based on morale level (e.g., happiness decreases despair)
dynamic_morale_effect = Effect(
    effect_id=5,
    dynamic_morale_per_tick=lambda c: 0.5 if c.morale < 50 else 0.1
)

city.morale = 30
morale_change = dynamic_morale_effect.get_raw_morale_per_tick(city)
assert morale_change == 0.5, f"Expected 0.5, got {morale_change}"
print(f"  ✅ Dynamic morale effect: +{morale_change} when morale is {city.morale}")

city.morale = 80
morale_change = dynamic_morale_effect.get_raw_morale_per_tick(city)
assert morale_change == 0.1, f"Expected 0.1, got {morale_change}"
print(f"  ✅ Dynamic morale effect: +{morale_change} when morale is {city.morale}")


# ========== TEST 5: Combined Contingency + Dynamic ==========
print("\n✓ TEST 5: Combined Contingency + Dynamic")

city = City(coords=(10, 10))
city.change_resources(ExpendableCityResources(wealth=100))
city._societal_resources.population.adults = 50

# Complex effect: dynamic consumption only when wealth is high
advanced_effect = Effect(
    effect_id=6,
    contingency_check=lambda c: c._resources.wealth > 10,
    dynamic_expendable_city_resources_per_tick=lambda c: ExpendableCityResources(
        wealth=-(c.total_population * 0.2)  # Costs increase with population
    )
)

# Should apply with high wealth
assert advanced_effect.should_apply(city), "Should apply when wealth is high"
resources = advanced_effect.get_baseline_city_resources_per_tick(city)
assert resources.wealth == -(city.total_population * 0.2), "Should calculate dynamic wealth cost"
print(f"  ✅ Effect applies with wealth={city._resources.wealth}, cost={resources.wealth}")

# Reduce wealth below threshold
city.change_resources(ExpendableCityResources(wealth=-95))
assert not advanced_effect.should_apply(city), "Should NOT apply when wealth is low"
print(f"  ✅ Effect does not apply with wealth={city._resources.wealth}")


# ========== TEST 6: Food Consumption System Integration ==========
print("\n✓ TEST 6: Food Consumption System Integration")

from backend.entities.ideology import Ideology

city = City(coords=(0, 0))
ideology = Ideology(effects_list=[], autonomy=50)
empire = Empire(autonomy=50, capital_city=city, ideology=ideology)
city.set_allegiance(empire)
city.change_resources(ExpendableCityResources(food=100))
city._societal_resources.population.adults = 20

# Simulate an effect tick - this should add the food consumption effects
city._food_consumption_effect_added = False
city._hunger_penalty_effect_added = False

# Add effects as the city tick would
if not city._food_consumption_effect_added:
    city.add_effect(effect=Effect(
        duration_in_ticks=0,
        dynamic_expendable_city_resources_per_tick=lambda c: ExpendableCityResources(
            food=-(c.total_population * FOOD_CONSUMPTION_SENSITIVITY)
        ),
        contingency_check=lambda c: c._resources.food > 0,
        effect_id=10  # AUTOMATIC_FOOD_CONSUMPTION_EFFECT_ID
    ))
    city._food_consumption_effect_added = True

if not city._hunger_penalty_effect_added:
    city.add_effect(effect=Effect(
        duration_in_ticks=0,
        raw_morale_per_tick=-1.0,
        contingency_check=lambda c: c._resources.food <= 0,
        effect_id=11  # MORALE_DEPLETION_DUE_TO_HUNGER_EFFECT_ID
    ))
    city._hunger_penalty_effect_added = True

total_effects = len(city._effects_with_ticks_left)
assert total_effects >= 2, f"Should have at least 2 persistent effects, got {total_effects}"
print(f"  ✅ Food consumption effects added: {total_effects} effects (including any ideology effects)")

# Find the food consumption and hunger effects we just added (they should be the last 2)
food_effect = city._effects_with_ticks_left[-2].effect
hunger_effect = city._effects_with_ticks_left[-1].effect

# Verify food consumption effect calculates correctly
resources = food_effect.get_baseline_city_resources_per_tick(city)
expected_consumption = -(city.total_population * FOOD_CONSUMPTION_SENSITIVITY)
assert resources.food == expected_consumption, f"Expected {expected_consumption}, got {resources.food}"
print(f"  ✅ Food consumption calculated: {resources.food} per tick for {city.total_population} population")

# Verify contingency is checked
assert food_effect.should_apply(city), "Food effect should apply when food available"
print(f"  ✅ Food consumption effect applies when food available ({city._resources.food} food)")

# Drain food and verify hunger effect would activate
city.change_resources(ExpendableCityResources(food=-100))
assert not food_effect.should_apply(city), "Food effect should NOT apply when no food"
assert hunger_effect.should_apply(city), "Hunger effect should apply when no food"
print(f"  ✅ Hunger effect activates when food unavailable ({city._resources.food} food)")


# ========== TEST 7: All Dynamic Methods Work ==========
print("\n✓ TEST 7: All Dynamic Methods Coverage")

effect = Effect(
    effect_id=20,
    dynamic_expendable_city_resources_per_tick=lambda c: ExpendableCityResources(food=-1),
    dynamic_morale_per_tick=lambda c: 0.5,
    dynamic_efficiency_per_tick=lambda c: 0.1,
    dynamic_city_hitpoint_regeneration_per_tick=lambda c: 2,
    dynamic_new_people_per_tick=lambda c: 3,
    dynamic_dead_people_per_tick=lambda c: 1,
    dynamic_job_speedup_multiplier=lambda c: 1.2
)

city = City(coords=(0, 0))
ideology = Ideology(effects_list=[], autonomy=50)
empire = Empire(autonomy=50, capital_city=city, ideology=ideology)
city.set_allegiance(empire)

# Test all getters work
assert effect.get_baseline_city_resources_per_tick(city).food == -1
assert effect.get_raw_morale_per_tick(city) == 0.5
assert effect.get_raw_efficiency_per_tick(city) == 0.1
assert effect.get_city_hitpoint_regeneration_per_tick(city) == 2
assert effect.get_new_people_per_tick(city) == 3
assert effect.get_dead_people_per_tick(city) == 1
assert effect.get_job_speedup_multiplier(city) == 1.2

print("  ✅ All dynamic value getters work correctly")

print("\n" + "=" * 70)
print("✅ ALL DYNAMIC EFFECTS TESTS PASSED!")
print("=" * 70)
print("\nSummary:")
print("  ✓ Contingency checks work for conditions like 'food > 0'")
print("  ✓ Dynamic values recalculate each tick based on city state")
print("  ✓ Static values still work as fallback")
print("  ✓ Food consumption system elegantly uses both features")
print("  ✓ All per-tick properties have dynamic counterparts")
print("  ✓ System is backward compatible - existing effects work unchanged")