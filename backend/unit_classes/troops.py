from ..army import Troop, ArmyAttributes
from ..data import ExpendableCityResources, ExpendableEmpireResources
from ..effects import Effect
from ..job_requirements import ContingentOnInfo, JobRequirements
from .buildings import Barracks

class Archer(Troop):
    name = "Archer"
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