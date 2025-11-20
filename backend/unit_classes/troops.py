"""
Military troop unit types.

Troops are combat units that deal damage and participate in battles.
They derive from MobileUnit and can be grouped into MobileUnitGroups (armies).
"""

from ..entities.army import Troop, ArmyAttributes
from ..systems.data import ExpendableCityResources
from ..systems.effects import Effect
from ..systems.job_requirements import ContingentOnInfo, JobRequirements
from .buildings import Barracks


class Archer(Troop):
    """
    A ranged combat troop that deals moderate damage.
    
    Archers require a Barracks to be produced and consume ongoing resources.
    """
    name = "Archer"
    size = 3
    job_num_ticks = 12
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
        workers_needed_level1=0,
        unit_types_contingent_on=[ContingentOnInfo(
            unit_class=Barracks,
            minimum_level_needed=1
        )]
    )
    base_attributes = ArmyAttributes(
        hitpoints=2,
        speed=5,
        damage_per_tick=1
    )
    description = "A good old fashion archer."
    
    def __init__(self):
        super().__init__()