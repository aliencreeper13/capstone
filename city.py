from __future__ import annotations # avoid circular import error

from math import ceil

from constants import FOOD_CONSUMPTION_SENSITIVITY, LACK_OF_FOOD_MORALE_PENALTY, MAX_MORALE
from empire import Empire, EmptyEmpire
from data import ExpendableCityResources, Population, SocietalResources
from building import Building
from typing import Optional
from queue import Queue

from exceptions import RequirementsExeption
from gameobject import GameObject
from job import Job
from effects import EffectWithTicksleft, Effect
from job_requirements import JobRequirements
from utils import new_value_given_morale

class City(GameObject):
    def __init__(self, size: int = 5, morale: float = 50.0):
        self.resources: ExpendableCityResources = ExpendableCityResources()
        self.societal_resources: SocietalResources = SocietalResources()
        self._defense = 100
        self._allegiance: Optional[Empire] = None # start off with no allegiance
        self._size = size
        self._morale = morale

        self._buildings: list[Building] = []
        self._running_jobs: list[Job] = [] # represents all running jobs (construction, etc.)

        # {`ticks left until finished`: effect}
        self._effect_with_ticks_left: list[EffectWithTicksleft] = []
        self._armies = []

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
        base_defense = self._defense
        for effect_with_tick_left in self._effect_with_ticks_left:
            if not effect_with_tick_left.is_finished():
                base_defense += effect_with_tick_left.effect.defense_offered

        return base_defense
    
    @property
    def knowledge(self):
        return self.allegiance.knowledge
    
    def gain_knowledge(self, value): 
        self.gain_knowledge += value

    @property
    def total_population(self) -> int: 
        return self.societal_resources.population.total()
    
    @property
    def current_tick(self):
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

    def change_resources(self, delta_city_resources: ExpendableCityResources):
        self.resources.food += delta_city_resources.food
        self.resources.timber += delta_city_resources.timber
        self.resources.metal += delta_city_resources.metal
        self.resources.wealth += delta_city_resources.wealth

        if self.resources.food <= 0:
            self.resources.food = 0
        if self.resources.timber <= 0:
            self.resources.timber = 0
        if self.resources.metal <= 0:
            self.resources.metal = 0
        if self.resources.wealth <= 0:
            self.resources.wealth = 0

    def expend_resources(self, city_resources: ExpendableCityResources):
        self.resources.food -= city_resources.food
        self.resources.timber -= city_resources.timber
        self.resources.metal -= city_resources.metal
        self.resources.wealth -= city_resources.wealth

        if self.resources.food <= 0:
            self.resources.food = 0
        if self.resources.timber <= 0:
            self.resources.timber = 0
        if self.resources.metal <= 0:
            self.resources.metal = 0
        if self.resources.wealth <= 0:
            self.resources.wealth = 0
    # todo: implement this methods
    def _apply_effect(self, effect: Effect, ticks_elapsed=1):
        
        
        if effect.capital_effect and not self.is_capital():  # do not apply effect if not capital city
            return
        
        # affect material resources. The rates given by the effects object are the baseline rate when morale=50
        self.change_resources(
            ExpendableCityResources(
                food=new_value_given_morale(effect.material_resources_per_tick.food, self.morale),
                timber=new_value_given_morale(effect.material_resources_per_tick.timber, self.morale),
                metal=new_value_given_morale(effect.material_resources_per_tick.metal, self.morale),
                wealth=new_value_given_morale(effect.material_resources_per_tick.wealth, self.morale)
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

            units_contingent_on =  requirements.contingent_on
            for unit_ in units_contingent_on:
                if not unit_.is_active(): # a single inactive unit means job can't start
                    return False

            food_excess = self.resources.food - requirements.food(level=1)
            timber_excess = self.resources.timber - requirements.timber(level=1)
            wealth_excess = self.resources.wealth - requirements.wealth(level=1)
            metal_excess = self.resources.metal - requirements.metal(level=1)
            
            if food_excess < 0 or timber_excess < 0 or wealth_excess < 0 or metal_excess < 0:
                return False
            else:
                return True
        if check_requirements(job):
            
            self._running_jobs.append(job)
        else:
            raise RequirementsExeption()
            
        return

    def update(self):
        print(self.resources)
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
                self.expend_resources(job.result.creation_job_requirements.city_resources(level=1)) 
                print("Buildings:", self._buildings)

        # food consumption effect: The higher the population, the more food gets consumed
        if self.resources.food > 0:
            self.add_effect(Effect(
                duration_in_ticks=1,
                material_resources_per_tick=ExpendableCityResources(food=-(self.total_population * FOOD_CONSUMPTION_SENSITIVITY))
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