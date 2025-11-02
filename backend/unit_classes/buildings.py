from ..building import Building
from ..data import ExpendableCityResources, ExpendableEmpireResources
from ..effects import Effect
from ..job_requirements import JobRequirements


class Market(Building):
    name = "Market"
    size = 3
    effect = Effect(
        duration_in_ticks=0,
        expendable_city_resources_per_tick=ExpendableCityResources(
            wealth=10
        )
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=1,
            timber=2,
        ),
        workers_needed_level1=3
    )
    description = "Periodically creates wealth for the city."
        
class Farm(Building):
    name = "Farm"
    size = 1
    effect = Effect(
        duration_in_ticks=0,
        expendable_city_resources_per_tick=ExpendableCityResources(
            food=1
        )
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=1,
            timber=1,
        ),
        workers_needed_level1=1
    )
    description = "Periodically creates food for the city."
        
class Granary(Building):
    name = "Granary"
    size = 3
    effect = Effect(
        duration_in_ticks=0,
        expendable_city_resource_capacities_offered=ExpendableCityResources(
            food=100
        )
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=10,
            timber=50,
        ),
        workers_needed_level1=3
    )
    description = "Adds more food storage for the city."
        

class WoodcuttersCamp(Building):
    name = "Woodcutter's Camp"
    size = 3
    effect = Effect(
        duration_in_ticks=0,
        expendable_city_resources_per_tick=ExpendableCityResources(
            timber=1
        )
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=1,
            food=1,
        ),
        workers_needed_level1=1
    )
    description = "Periodically creates timber for the city."
        
class LumberYard(Building):
    name = "Lumber Yard"
    size = 3
    effect = Effect(
        duration_in_ticks=0,
        expendable_city_resource_capacities_offered=ExpendableCityResources(
            timber=100
        )
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=10,
            food=50,
        ),
        workers_needed_level1=3
    )
    description = "Adds more timber storage for the city."
        
class Mine(Building):
    name = "Mine"
    size = 1
    effect = Effect(
        duration_in_ticks=0,
        expendable_city_resources_per_tick=ExpendableCityResources(
            metal=1
        )
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=2,
        ),
        workers_needed_level1=1
    )
    description = "Periodically creates metal for the city."
        
class FoundryVault(Building):
    name = "Foundry Vault"
    size = 3
    effect = Effect(
        duration_in_ticks=0,
        expendable_city_resource_capacities_offered=ExpendableCityResources(
            metal=100
        )
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=10,
            food=50,
        ),
        workers_needed_level1=3
    )
    description = "Adds more metal storage for the city."
        
class School(Building):
    name = "School"
    size = 1
    effect = Effect(
        duration_in_ticks=0,
        expendable_empire_resources_per_tick=ExpendableEmpireResources(
            knowledge=1
        ),
        raw_morale_per_tick=0.1
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=2,
        ),
        workers_needed_level1=1
    )
    description = "Periodically creates little knowledge and little morale for the city. Trains people for work."

class University(Building):
    name = "University"
    size = 4
    effect = Effect(
        duration_in_ticks=0,
        expendable_empire_resources_per_tick=ExpendableEmpireResources(
            knowledge=100
        )
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=200,
        ),
        workers_needed_level1=1,
        max_per_city=1
    )
    description = "Periodically creates knowledge for the city. Trains people for work. Only one allowed per city."
        
class Library(Building):
    name = "Library"
    size = 1
    effect = Effect(
        duration_in_ticks=0,
        raw_morale_per_tick=0.025
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=1,
            timber=10
        ),
        workers_needed_level1=2,
        max_per_city=1
    )
    description = "Morale booster for city"
        
class Temple(Building):
    name = "Temple"
    size = 1
    effect = Effect(
        duration_in_ticks=0,
        raw_morale_per_tick=0.025
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=1,
            timber=10
        ),
        workers_needed_level1=2,
        max_per_city=2
    )
    description = "Morale booster for city"

class Hospital(Building):
    name = "Hospital"
    size = 4
    effect = Effect(
        duration_in_ticks=0,
        raw_morale_per_tick=0.05,
        max_lifespan_increase=10  # Increases maximum population lifespan by 10 years
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=1,
            timber=10
        ),
        workers_needed_level1=2,
        max_per_city=2
    )
    description = "Morale booster for city, increases lifespan."
        
class Housing(Building):
    name = "Housing"
    size = 2
    effect = Effect(
        duration_in_ticks=0,
        population_capacity_offered=100
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=1,
            timber=1,
            food=1,
            metal=1
        ),
        workers_needed_level1=2,
        max_per_city=1
    )
    description = "Increases population limit for city."


#############################################################################
# MILITARY BUILDINGS
#############################################################################

class Barracks(Building):
    name = "Barracks"
    size = 2
    effect = Effect(
        duration_in_ticks=0,
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=10,
            timber=10,
            food=10,
        ),
        workers_needed_level1=3,
        max_per_city=None
    )
    description = "Enables creation of foot troops."
        
class Stable(Building):
    name = "Stable"
    size = 2
    effect = Effect(
        duration_in_ticks=0,
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=15,
            timber=30,
            food=20,
        ),
        workers_needed_level1=5,
        max_per_city=None
    )
    description = "Enables creation of calvary."
        
class Fortress(Building):
    name = "Fortress"
    size = 5
    effect = Effect(
        duration_in_ticks=0,
        city_base_protection_offered=500,
        city_base_defense_offered=200
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=150,
            timber=50,
            metal=50,
        ),
        workers_needed_level1=15,
        max_per_city=1
    )
    description = "strongly boosts city defense"
        
class Walls(Building):
    name = "Walls"
    size = 0  # this is not a typo, walls do not take up space
    effect = Effect(
        duration_in_ticks=0,
        city_base_protection_offered=10
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=1,
            timber=5,
            metal=5,
        ),
        workers_needed_level1=2,
        max_per_city=1
    )
    description = "strongly boosts city defense"