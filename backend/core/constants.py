"""
Game constants and configuration values.
Contains tunable parameters for game balance and mechanics.
"""

# Morale System
MAX_MORALE: float = 100.0
HALF_MORALE: float = MAX_MORALE / 2
MORALE_REVOLT_THRESHOLD: float = 0.005  # Displayed morale below this triggers revolt (low morale period)

# Autonomy System
MAX_AUTONOMY: int = 100
HALF_AUTONOMY: int = MAX_AUTONOMY // 2

# Resource Management
FOOD_CONSUMPTION_SENSITIVITY = 0.01
LACK_OF_FOOD_MORALE_PENALTY = 0.01

# Population System
BASELINE_MORALE_DEGRADATION = 0.05  # Natural morale decrease per tick (to balance effects)
POPULATION_GROWTH_BASE_RATE = 0.02  # Base growth rate (0.02 = 2% per tick with ideal conditions)
POPULATION_GROWTH_MORALE_THRESHOLD = 60  # Morale needed for population growth to occur
POPULATION_GROWTH_MORALE_BONUS = 0.005  # Extra growth per morale point above threshold
POPULATION_DEATH_RATE_WHEN_NO_FOOD = 0.05  # Death rate if no food available (5% per tick)

# Building System
BUILDING_REFUND = 0.3  # e.g. 0.3 = 30% of building's costs will be refunded upon destruction of building

# Unit System
DESTRUCTION_WEALTH_COST_PER_UNIT_SIZE = 10

# Effect IDs (for unique effect identification)
AUTOMATIC_FOOD_CONSUMPTION_EFFECT_ID = 0
MORALE_DEPLETION_DUE_TO_HUNGER_EFFECT_ID = 1

# Government Actions - Tax Levels
TAX_INTENSITY_1_MORALE_PENALTY = 10
TAX_INTENSITY_1_WEALTH_GAIN = 5
TAX_INTENSITY_1_DURATION = 5

TAX_INTENSITY_2_MORALE_PENALTY = 25
TAX_INTENSITY_2_WEALTH_GAIN = 12
TAX_INTENSITY_2_DURATION = 5

TAX_INTENSITY_3_MORALE_PENALTY = 50.0
TAX_INTENSITY_3_WEALTH_GAIN = 25
TAX_INTENSITY_3_DURATION = 5

# Government Actions - Subsidy
SUBSIDY_DEFAULT_COST = 20
SUBSIDY_DEFAULT_SPEEDUP = 2.0
SUBSIDY_SPEEDUP_MIN = 0.5
SUBSIDY_SPEEDUP_MAX = 5.0
SUBSIDY_DEFAULT_DURATION = 5

# Government Actions - Elections
ELECTION_COST = 10
ELECTION_DURATION = 3
ELECTION_MORALE_BOOST = 3.0

# Government Actions - Propaganda
PROPAGANDA_PATRIOTIC_COST = 15
PROPAGANDA_PATRIOTIC_DURATION = 4
PROPAGANDA_PATRIOTIC_MORALE = 2
PROPAGANDA_PATRIOTIC_WEALTH = 2

PROPAGANDA_ECONOMIC_COST = 20
PROPAGANDA_ECONOMIC_DURATION = 5
PROPAGANDA_ECONOMIC_MORALE = -1
PROPAGANDA_ECONOMIC_WEALTH = 5

PROPAGANDA_POPULIST_COST = 15
PROPAGANDA_POPULIST_DURATION = 4
PROPAGANDA_POPULIST_MORALE = 3
PROPAGANDA_POPULIST_POPULATION = 5

PROPAGANDA_ENVIRONMENTAL_COST = 12
PROPAGANDA_ENVIRONMENTAL_DURATION = 4
PROPAGANDA_ENVIRONMENTAL_FOOD = 3
PROPAGANDA_ENVIRONMENTAL_TIMBER = 3

# Revolt System
REVOLT_COUNTDOWN_WHEN_MORALE_ZERO = 10  # Ticks before revolt happens after morale hits 0
REVOLT_COUNTDOWN_INSTANT = 0  # Special value to trigger immediate revolt

# Resource Transfer System
RESOURCE_TRANSFER_WEALTH_COST_PER_TILE = 0.1  # Wealth cost to transfer per tile distance
RESOURCE_TRANSFER_TICKS_PER_TILE = 1  # Ticks to transfer per tile distance