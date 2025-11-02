"""
Game systems package containing game mechanics, data structures, and effects processing.
This package handles:
- Data classes for resources and population (data.py)
- Effects system for applying game impacts (effects.py)
- Job requirements and job processing (job_requirements.py, job.py)
- Game balance calculations and utilities (game_utils.py)
"""

from .data import (
    GameDataclass,
    ExpendableCityResources,
    Population,
    SocietalResources,
    ExpendableEmpireResources,
)

from .effects import (
    Effect,
    UniversalEffect,
    EffectWithTicksLeft,
)

from .job_requirements import (
    JobRequirements,
    ContingentOnInfo,
    HasJobRequirementsMixin,
)

from .game_utils import (
    new_value_given_morale,
)

__all__ = [
    "GameDataclass",
    "ExpendableCityResources",
    "Population",
    "SocietalResources",
    "ExpendableEmpireResources",
    "Effect",
    "UniversalEffect",
    "EffectWithTicksLeft",
    "JobRequirements",
    "ContingentOnInfo",
    "HasJobRequirementsMixin",
    "new_value_given_morale",
]