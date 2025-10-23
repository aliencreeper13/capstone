from engine.army import ArmyUnit, ArmyAttributes
from engine.data import ExpendableCityResources, ExpendableEmpireResources
from engine.effects import Effect
from engine.job_requirements import ContingentOnInfo, JobRequirements
from engine.unit_classes.buildings import Barracks

class Archer(ArmyUnit):
    name = "Archer"
    size = 3
    effects = Effect(
        duration_in_ticks=0,
        expendable_city_resources_per_tick=ExpendableCityResources(
            wealth=10
        )
    )
    job_requirements = JobRequirements(
        city_resources_level1=ExpendableCityResources(
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