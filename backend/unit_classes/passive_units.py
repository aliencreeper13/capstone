"""
Passive unit types for non-combat, special-purpose units.

Passive units have 0 damage and provide benefits like settlement capabilities,
resource gathering, or support functions.
"""

from ..entities.mobile_unit import CombatAttributes
from ..entities.passive import PassiveUnit
from ..systems.data import ExpendableCityResources
from ..systems.effects import Effect
from ..systems.job_requirements import JobRequirements


class Settler(PassiveUnit):
    """
    A settler unit that can establish new cities on unclaimed game nodes.
    
    When 10 or more Settlers are stationed on an unclaimed GameNode,
    the node automatically converts into a new City belonging to the empire.
    Settlers move like troops but have 0 damage and serve a colonization function.
    """
    name = "Settler"
    size = 1
    effect = Effect(
        duration_in_ticks=0,
    )
    job_requirements = JobRequirements(
        expendable_city_resources_level1=ExpendableCityResources(
            wealth=100,
            food=100,
        ),
        workers_needed_level1=0,
        unit_types_contingent_on=[]
    )
    base_attributes = CombatAttributes(
        hitpoints=20,
        speed=5,
        damage_per_tick=0  # passive unit, does not deal damage
    )
    description = "A settler is a special worker that establishes new cities on unclaimed land."
    
    def __init__(self):
        super().__init__()