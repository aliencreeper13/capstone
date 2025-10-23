from engine.building import Building
from engine.data import ExpendableCityResources, ExpendableEmpireResources
from engine.effects import Effect
from engine.job_requirements import JobRequirements


class Market(Building):
    def __init__(self):
        super().__init__(name=type(self).__name__, # set name to name of class
                         size=3, 
                         effects=Effect(
                             duration_in_ticks=0,
                             expendable_city_resources_per_tick=ExpendableCityResources(
                                 wealth=10
                             )
                         ), 
                         requirements=JobRequirements(
                             city_resources_level1=ExpendableCityResources(
                                 wealth=1,
                                 timber=2,
                             ),
                             workers_needed_level1=3
                         ),
                         description="Periodically creates wealth for the city.")
        
class Farm(Building):
    def __init__(self):
        super().__init__(name=type(self).__name__, # set name to name of class
                         size=1, 
                         effects=Effect(
                             duration_in_ticks=0,
                             expendable_city_resources_per_tick=ExpendableCityResources(
                                 food=1
                             )
                         ), 
                         requirements=JobRequirements(
                             city_resources_level1=ExpendableCityResources(
                                 wealth=1,
                                 timber=1,
                             ),
                             workers_needed_level1=1
                         ),
                         description="Periodically creates food for the city.")
        
class Granary(Building):
    def __init__(self):
        super().__init__(name=type(self).__name__, # set name to name of class 
                         size=3, 
                         effects=Effect(
                             duration_in_ticks=0,
                             expendable_city_resource_capacities_offered=ExpendableCityResources(
                                 food=100
                             )
                         ), 
                         requirements=JobRequirements(
                             city_resources_level1=ExpendableCityResources(
                                 wealth=10,
                                 timber=50,
                             ),
                             workers_needed_level1=3
                         ),
                         description="Adds more food storage for the city.")
        

class WoodcuttersCamp(Building):
    def __init__(self):
        super().__init__(name="Woodcutter's Camp",
                         size=3, 
                         effects=Effect(
                             duration_in_ticks=0,
                             expendable_city_resources_per_tick=ExpendableCityResources(
                                 timber=1
                             )
                         ), 
                         requirements=JobRequirements(
                             city_resources_level1=ExpendableCityResources(
                                 wealth=1,
                                 food=1,
                             ),
                             workers_needed_level1=1
                         ),
                         description="Periodically creates timber for the city.")
        
class LumberYard(Building):
    def __init__(self):
        super().__init__(name="Lumber Yard",
                         size=3, 
                         effects=Effect(
                             duration_in_ticks=0,
                             expendable_city_resource_capacities_offered=ExpendableCityResources(
                                 timber=100
                             )
                         ), 
                         requirements=JobRequirements(
                             city_resources_level1=ExpendableCityResources(
                                 wealth=10,
                                 food=50,
                             ),
                             workers_needed_level1=3
                         ),
                         description="Adds more timber storage for the city.")
        
class Mine(Building):
    def __init__(self):
        super().__init__(name=type(self).__name__, # set name to name of class
                         size=1, 
                         effects=Effect(
                             duration_in_ticks=0,
                             expendable_city_resources_per_tick=ExpendableCityResources(
                                 metal=1
                             )
                         ), 
                         requirements=JobRequirements(
                             city_resources_level1=ExpendableCityResources(
                                 wealth=2,
                             ),
                             workers_needed_level1=1
                         ),
                         description="Periodically creates metal for the city.")
        
class FoundryVault(Building):
    def __init__(self):
        super().__init__(name="Foundary Vault",
                         size=3, 
                         effects=Effect(
                             duration_in_ticks=0,
                             expendable_city_resource_capacities_offered=ExpendableCityResources(
                                 timber=100
                             )
                         ), 
                         requirements=JobRequirements(
                             city_resources_level1=ExpendableCityResources(
                                 wealth=10,
                                 food=50,
                             ),
                             workers_needed_level1=3
                         ),
                         description="Adds more metal storage for the city.")
        
class School(Building):
    def __init__(self):
        super().__init__(name=type(self).__name__, # set name to name of class
                         size=1, 
                         effects=Effect(
                             duration_in_ticks=0,
                             expendable_empire_resources_per_tick=ExpendableEmpireResources(
                                 knowledge=1
                             ),
                             morale_per_tick=0.1
                         ), 
                         requirements=JobRequirements(
                             city_resources_level1=ExpendableCityResources(
                                 wealth=2,
                             ),
                             workers_needed_level1=1
                         ),
                         description="Periodically creates little knowledge and little morale for the city. Trains people for work.")

class University(Building):
    def __init__(self):
        super().__init__(name=type(self).__name__, # set name to name of class
                         size=4, 
                         effects=Effect(
                             duration_in_ticks=0,
                             expendable_empire_resources_per_tick=ExpendableEmpireResources(
                                 knowledge=100
                             )
                         ), 
                         requirements=JobRequirements(
                             city_resources_level1=ExpendableCityResources(
                                 wealth=200,
                             ),
                             workers_needed_level1=1,
                             max_per_city=1
                         ),
                         description="Periodically creates knowledge for the city. Trains people for work. Only one allowed per city.")
        
class Library(Building):
    def __init__(self):
        super().__init__(name=type(self).__name__, # set name to name of class
                         size=1, 
                         effects=Effect(
                             duration_in_ticks=0,
                             morale_per_tick=0.025
                         ), 
                         requirements=JobRequirements(
                             city_resources_level1=ExpendableCityResources(
                                 wealth=1,
                                 timber=10
                             ),
                             workers_needed_level1=2,
                             max_per_city=1
                         ),
                         description="Morale booster for city")
        
class Temple(Building):
    def __init__(self):
        super().__init__(name=type(self).__name__, # set name to name of class
                         size=1, 
                         effects=Effect(
                             duration_in_ticks=0,
                             morale_per_tick=0.025
                         ), 
                         requirements=JobRequirements(
                             city_resources_level1=ExpendableCityResources(
                                 wealth=1,
                                 timber=10
                             ),
                             workers_needed_level1=2,
                             max_per_city=2
                         ),
                         description="Morale booster for city")

# todo: add effect for increasing lifespan
class Hosptial(Building):
    def __init__(self):
        super().__init__(name=type(self).__name__, # set name to name of class
                         size=4, 
                         effects=Effect(
                             duration_in_ticks=0,
                             morale_per_tick=0.05
                         ), 
                         requirements=JobRequirements(
                             city_resources_level1=ExpendableCityResources(
                                 wealth=1,
                                 timber=10
                             ),
                             workers_needed_level1=2,
                             max_per_city=2
                         ),
                         description="Morale booster for city, increases lifespan.")
        
class Housing(Building):
    def __init__(self):
        super().__init__(name=type(self).__name__, # set name to name of class
                         size=2, 
                         effects=Effect(
                             duration_in_ticks=0,
                             population_capacity_offered=100
                         ), 
                         requirements=JobRequirements(
                             city_resources_level1=ExpendableCityResources(
                                 wealth=1,
                                 timber=1,
                                 food=1,
                                 metal=1
                             ),
                             workers_needed_level1=2,
                             max_per_city=1
                         ),
                         description="Increases population limit for city.")


#############################################################################
# MILITARY BUILDINGS
#############################################################################

class Barracks(Building):
    def __init__(self):
        super().__init__(name=type(self).__name__, # set name to name of class
                         size=2, 
                         effects=Effect(
                             duration_in_ticks=0,
                         ), 
                         requirements=JobRequirements(
                             city_resources_level1=ExpendableCityResources(
                                 wealth=10,
                                 timber=10,
                                 food=10,
                             ),
                             workers_needed_level1=3,
                             max_per_city=None
                         ),
                         description="Enables creation of foot troops.")
        
class Stable(Building):
    def __init__(self):
        super().__init__(name=type(self).__name__, # set name to name of class
                         size=2, 
                         effects=Effect(
                             duration_in_ticks=0,
                         ), 
                         requirements=JobRequirements(
                             city_resources_level1=ExpendableCityResources(
                                 wealth=15,
                                 timber=30,
                                 food=20,
                             ),
                             workers_needed_level1=5,
                             max_per_city=None
                         ),
                         description="Enables creation of calvary.")
        
class Fortress(Building):
    def __init__(self):
        super().__init__(name=type(self).__name__, # set name to name of class
                         size=5, 
                         effects=Effect(
                             duration_in_ticks=0,
                             defense_offered=200
                         ), 
                         requirements=JobRequirements(
                             city_resources_level1=ExpendableCityResources(
                                 wealth=150,
                                 timber=50,
                                 metal=50,
                             ),
                             workers_needed_level1=15,
                             max_per_city=1
                         ),
                         description="strongly boosts city defense")
        
class Walls(Building):
    def __init__(self):
        super().__init__(name=type(self).__name__, # set name to name of class
                         size=0,  # this is not a typo, walls do not take up space 
                         effects=Effect(
                             duration_in_ticks=0,
                             defense_offered=10
                         ), 
                         requirements=JobRequirements(
                             city_resources_level1=ExpendableCityResources(
                                 wealth=1,
                                 timber=5,
                                 metal=5,
                             ),
                             workers_needed_level1=2,
                             max_per_city=1
                         ),
                         description="strongly boosts city defense")