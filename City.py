from __future__ import annotations # avoid circular import error

from Empire import Empire, EmptyEmpire
from data import MaterialResources, Population, SocietalResources
from building import Building
from typing import Optional
from queue import Queue

from job import Job
from effects import EffectWithTicksleft, Effects
from utils import new_production_rate_given_morale

class City:
    def __init__(self, capital=False, size: int = 5, morale: int = 50):
        self.resources: MaterialResources = MaterialResources()
        self.societal_resources: SocietalResources = SocietalResources()
        self.defense = 100
        self.capital = capital
        self._allegiance: Empire = EmptyEmpire() # start off with no allegiance
        self._size = size
        self._morale = morale

        self._buildings: list[Building] = []
        self._running_jobs: list[Job] = [] # represents all running jobs (construction, etc.)

        # {`ticks left until finished`: effect}
        self._effects: list[EffectWithTicksleft] = []

    # this runs every tick
    def mainloop():
        pass

    @property
    def allegiance(self):
        return self._allegiance
    
    # the autonomy of a city is the autonomy permitted by the empire
    @property
    def autonomy(self):
        return self.allegiance.autonomy
    
    @property
    def knowledge(self):
        return self.allegiance.knowledge
    
    def gain_knowledge(self, value): 
        self.gain_knowledge += value
    
    @property
    def current_tick(self):
        return self.allegiance.game.current_tick

    
    def set_allegiance(self, allegiance: Empire):
        self._allegiance = allegiance

    def declare_independence(self):
        self._allegiance = EmptyEmpire()

    def remove_as_capital(self):
        self.capital = False

    def set_as_capital(self):
        self.capital = True

    def _remaining_space(self) -> int:
        total_occupied_space: int = 0
        for building in self._buildings:
            total_occupied_space += building.size

        return self._size - total_occupied_space


    # private function
    def _add_building(self, building: Building):
        assert self._remaining_space() > 0

        assert not building in self._buildings

        self._buildings.append(building)
        self._effects.append(EffectWithTicksleft(effects=building.effects, 
                                                 ticks_left=building.effects.duration_in_ticks))  # add building's effects

    def _upgrade_building(self, building: Building):
        assert building in self._buildings

        building.upgrade() # when the building is upgraded, the effects upgraded as well
        

    @property
    def morale(self) -> int:
        return self._morale

    @morale.setter
    def morale(self, new_morale: int):
        assert 0 <= new_morale <= 100
        self._morale = new_morale

    # todo: implement this methods
    def apply_effects(self, effects: Effects, ticks_elapsed=1):
        # affect material resources. The rates given by the effects object are the baseline rate when morale=50
        self.resources.food += new_production_rate_given_morale(effects.material_resources_per_tick.food, self.morale)
        self.resources.timber += new_production_rate_given_morale(effects.material_resources_per_tick.timber, self.morale)
        self.resources.metal += new_production_rate_given_morale(effects.material_resources_per_tick.metal, self.morale)
        self.resources.wealth += new_production_rate_given_morale(effects.material_resources_per_tick.wealth, self.morale)


        self._morale += effects.morale_per_tick

    def update(self):
        for job in self._running_jobs:
            job.progress()
            if job.is_finished():
                
                if isinstance(job.result, Building):
                    if job._is_upgrade():
                        self._upgrade_building(job.result)
                    else:
                        self._add_building(job.result)

                self._running_jobs.remove(job)

        for effects_with_ticks_left in (self._effects):
            self.apply_effects(effects_with_ticks_left.effects)
            effects_with_ticks_left.progress()
            if effects_with_ticks_left.is_finished():
                self._effects.remove(effects_with_ticks_left)
            

            

    

class EmptyCity(City):
    """
    A unit's allegiance to this city means that the unit has NO allegiance
    """
    # this makes this a singleton class
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(EmptyCity, cls).__new__(cls)
        return cls.instance