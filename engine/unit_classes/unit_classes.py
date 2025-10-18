from engine.building import Building
from engine.data import ExpendableCityResources
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