from __future__ import annotations # avoid circular import error

from math import ceil

from constants import FOOD_CONSUMPTION_SENSITIVITY, LACK_OF_FOOD_MORALE_PENALTY, MAX_MORALE
from empire import Empire, EmptyEmpire
from data import ExpendableCityResources, Population, SocietalResources, ExpendableEmpireResources
from building import Building
from typing import Optional
from queue import Queue

from exceptions import NotAssignedToGameException, NotEnoughWorkersException, RequirementsExeption
from gameobject import GameObject, client_property
from job import Job
from effects import EffectWithTicksleft, Effect
from job_requirements import JobRequirements
from location import GameNode
from utils import new_value_given_morale
import gameobject

class City(GameNode):
    def __init__(self, coords: tuple[int, int], size: int = 5, morale: float = 50.0):
        super().__init__(coords=coords, size=size)
        self._resources: ExpendableCityResources = ExpendableCityResources()
        self._base_resource_capacities: ExpendableCityResources = ExpendableCityResources(
            food=100,
            timber=100,
            wealth=100,
            metal=100
        )

        self._societal_resources: SocietalResources = SocietalResources()
        self._employed_people: int = 0 # number of people who are working
        self._defense = 100
        self._allegiance: Optional[Empire] = None # start off with no allegiance
        # self._size = size
        self._morale = morale

        self._buildings: list[Building] = []
        self._running_jobs: list[Job] = [] # represents all running jobs (construction, etc.)

        # {`ticks left until finished`: effect}
        self._effect_with_ticks_left: list[EffectWithTicksleft] = []

    def is_capital(self) -> bool:
        return self.allegiance.capital is self

    @property
    def allegiance(self):
        return self._allegiance
    
    # the autonomy of a city is the autonomy permitted by the empire
    @property
    def autonomy(self):
        return self.allegiance.autonomy
    
    @property
    def defense(self):
        total_defense = self._defense
        for effect_with_tick_left in self._effect_with_ticks_left:
            if not effect_with_tick_left.is_finished():
                total_defense += effect_with_tick_left.effect.defense_offered

        return total_defense
    
    @property
    def expendable_resource_capacities(self) -> ExpendableCityResources:
        resource_capacities = self._base_resource_capacities
        for effect_with_tick_left in self._effect_with_ticks_left:
            if not effect_with_tick_left.is_finished():
                resource_capacities.food += effect_with_tick_left.effect.expendable_city_resource_capacities_offered.food
                resource_capacities.timber += effect_with_tick_left.effect.expendable_city_resource_capacities_offered.timber
                resource_capacities.metal += effect_with_tick_left.effect.expendable_city_resource_capacities_offered.metal
                resource_capacities.wealth += effect_with_tick_left.effect.expendable_city_resource_capacities_offered.wealth
        return resource_capacities
    
    @client_property
    def knowledge(self) -> Optional[int]:
        if self.allegiance is None:
            return None
        return self.allegiance.knowledge
    
    
    
    
    def gain_knowledge(self, value): 
        self.gain_knowledge += value

    @gameobject.client_property
    def total_population(self) -> int: 
        return self._societal_resources.population.total()
    
    @property
    def employable_population(self) -> int:
        return self._societal_resources.employable_population
    
    def _employ_people(self, num_people: int):
        if (self._societal_resources.employable_population - num_people < 0):
            raise NotEnoughWorkersException()
        self._societal_resources.employable_population -= num_people
        self._societal_resources.employable_population += num_people

    def _lay_off_workers(self, num_people: int):
        if (self._societal_resources.employed_population - num_people < 0):
            raise NotEnoughWorkersException()
        self._societal_resources.employable_population += num_people
        self._societal_resources.employable_population -= num_people
    
    @gameobject.client_property
    # @property
    def current_tick(self):
        if self.allegiance is None:
            return None
        return self.allegiance.game.current_tick

    
    def set_allegiance(self, allegiance: Empire):
        self._allegiance = allegiance

    def declare_independence(self):
        self._allegiance = None

    def _remaining_space(self) -> int:
        total_occupied_space: int = 0
        for building in self._buildings:
            total_occupied_space += building.size

        return self._size - total_occupied_space
    
    def add_effect(self, effects: Effect):
        self._effect_with_ticks_left.append(EffectWithTicksleft(
            effect=effects,
            ticks_left=effects.duration_in_ticks
        ))


    def _destroy_building(self, building: Building):
        building.set_inactive()
        self._size += building.size
        self._buildings.remove(building)



    # private function
    def _add_building(self, building: Building):
        assert self._remaining_space() > 0

        assert not building in self._buildings

        self._buildings.append(building)
        self._size -= building.size
        building.set_city(self)
        self.add_effect(self, effects=building.effects)  # add building's effects

    def _upgrade_building(self, building: Building):
        assert building in self._buildings

        building.upgrade() # when the building is upgraded, the effects upgraded as well
        

    @property
    def morale(self) -> int:
        return self._morale

    @morale.setter
    def morale(self, new_morale: int):
        assert 0 <= new_morale <= MAX_MORALE
        self._morale = new_morale
    # fixme: we need to make this more efficient and less repetitive!!!!
    def change_resources(self, delta_city_resources: ExpendableCityResources):
        self._resources.food += delta_city_resources.food
        self._resources.timber += delta_city_resources.timber
        self._resources.metal += delta_city_resources.metal
        self._resources.wealth += delta_city_resources.wealth

        if self._resources.food <= 0:
            self._resources.food = 0
        if self._resources.timber <= 0:
            self._resources.timber = 0
        if self._resources.metal <= 0:
            self._resources.metal = 0
        if self._resources.wealth <= 0:
            self._resources.wealth = 0

        if self._resources.food > self.expendable_resource_capacities.food:
            self._resources.food = self.expendable_resource_capacities.food
        if self._resources.timber > self.expendable_resource_capacities.timber:
            self._resources.timber = self.expendable_resource_capacities.timber
        if self._resources.metal > self.expendable_resource_capacities.metal:
            self._resources.metal = self.expendable_resource_capacities.metal
        if self._resources.wealth > self.expendable_resource_capacities.wealth:
            self._resources.wealth = self.expendable_resource_capacities.wealth

    def expend_city_resources(self, city_resources: ExpendableCityResources):
        self._resources.food -= city_resources.food
        self._resources.timber -= city_resources.timber
        self._resources.metal -= city_resources.metal
        self._resources.wealth -= city_resources.wealth

        if self._resources.food <= 0:
            self._resources.food = 0
        if self._resources.timber <= 0:
            self._resources.timber = 0
        if self._resources.metal <= 0:
            self._resources.metal = 0
        if self._resources.wealth <= 0:
            self._resources.wealth = 0

    def change_empire_resources(self, empire_resources: ExpendableEmpireResources):
        pass

    def increase_population(self, new_people):
        pass

    # todo: implement this methods
    def _apply_effect(self, effect: Effect, ticks_elapsed=1):
        
        
        if effect.capital_effect and not self.is_capital():  # do not apply effect if not capital city
            return
        
        # affect material resources. The rates given by the effects object are the baseline rate when morale=50
        self.change_resources(
            ExpendableCityResources(
                food=new_value_given_morale(effect.expendable_city_resources_per_tick.food, self.morale),
                timber=new_value_given_morale(effect.expendable_city_resources_per_tick.timber, self.morale),
                metal=new_value_given_morale(effect.expendable_city_resources_per_tick.metal, self.morale),
                wealth=new_value_given_morale(effect.expendable_city_resources_per_tick.wealth, self.morale)
            )
        )
        self._morale += effect.morale_per_tick

    def _apply_all_effects(self):
        for effect_with_ticks_left in (self._effect_with_ticks_left):
            if not effect_with_ticks_left.effect.is_active():  # skip inactive effects
                continue
            self._apply_effect(effect_with_ticks_left.effect)
            effect_with_ticks_left.progress()
            if effect_with_ticks_left.is_finished():
                self._effect_with_ticks_left.remove(effect_with_ticks_left)
        

    def add_job(self, job: Job):
        # todo: make sure that the appropriate resources are present
        def check_requirements(job: Job) -> bool:
            """Returns True if requirements are satisfied. False otherwise"""
            requirements: JobRequirements = job.result.creation_job_requirements
            level = 1
            if job.is_upgrade():
                level = job.result.level + 1

            units_contingent_on =  requirements.contingent_on
            for unit_ in units_contingent_on:
                if not unit_.is_active(): # a single inactive unit means job can't start
                    return False

            food_excess = self._resources.food - requirements.food(level=level)
            timber_excess = self._resources.timber - requirements.timber(level=level)
            wealth_excess = self._resources.wealth - requirements.wealth(level=level)
            metal_excess = self._resources.metal - requirements.metal(level=level)

            workers_excess = self.employable_population - requirements.workers_needed(level=level)
            
            if food_excess < 0 or timber_excess < 0 or wealth_excess < 0 or metal_excess < 0 or workers_excess < 0:
                return False
            else:
                return True
        if check_requirements(job):
            level = 1
            if job.is_upgrade():
                level = job.result.level + 1
            self.expend_city_resources(job.result.creation_job_requirements.city_resources(level=level))
            self._employ_people(job.result.creation_job_requirements.workers_needed(level=level)) # employ people for job
            self._running_jobs.append(job)
        else:
            raise RequirementsExeption()
            
        return

    def update(self):
        print(self._resources)
        for job in self._running_jobs:
            # print("progressing job", job)
            job.progress()
            if job.is_finished():
                
                if isinstance(job.result, Building):
                    if job._is_upgrade:
                        self._upgrade_building(job.result)
                    else:
                        self._add_building(job.result)
                print("Finished job!")
                self._running_jobs.remove(job)

                self._lay_off_workers(job.result.creation_job_requirements.workers_needed(level=job.result.level))  # change this to reflect actual level
                
                print("Buildings:", self._buildings)

        # food consumption effect: The higher the population, the more food gets consumed
        if self._resources.food > 0:
            self.add_effect(Effect(
                duration_in_ticks=1,
                expendable_city_resources_per_tick=ExpendableCityResources(food=-(self.total_population * FOOD_CONSUMPTION_SENSITIVITY))
            ))
        # if there is no food left, then morale will be depleted
        else:
            self.add_effect(Effect(
                duration_in_ticks=1,
                morale_per_tick=-LACK_OF_FOOD_MORALE_PENALTY
            ))

        self._apply_all_effects()
                

    

class EmptyCity(City):
    """
    A unit's allegiance to this city means that the unit has NO allegiance
    """
    # this makes this a singleton class
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(EmptyCity, cls).__new__(cls)
        return cls.instance
    
if __name__ == "__main__":
    c = City((15, 24), 5, 50)
    # print(c.__dict__)
    c.current_tick
    print("POOP :)")
    print(c.to_client_json())