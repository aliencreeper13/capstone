"""
Backend package for civilization game.

This package contains the core game logic for the civilization game engine.
It has been refactored into a hierarchical 4-package architecture:

    - core/: Foundational classes and constants
        - constants: Game balance parameters
        - exceptions: Custom exceptions
        - gameobject: Base GameObject class
        - engine_utils: Core utility functions
    
    - systems/: Game systems (data, mechanics, jobs)
        - data: Resource and population data classes
        - effects: Effect application system
        - job_requirements: Job prerequisites
        - job: Job queue and execution system
        - game_utils: Morale calculations and utilities
    
    - entities/: Main game entities
        - building: Building base class and mechanics
        - city: City management (population, resources, buildings, jobs)
        - empire: Empire management (collection of cities)
        - unit: Unit base classes for buildings and troops
        - army: Army management and combat mechanics
        - ideology: Ideology system with bonuses/penalties
    
    - gameplay/: Game engine and mechanics
        - game: Main game loop and tick management
        - location: World map and location data structures
        - events: Game event system for tracking state transitions
    
    - unit_classes/: Specific implementations of buildings and units

Backward Compatibility:
    This module re-exports key classes from all packages to support both:
    1. Direct imports: from backend.core import constants
    2. Flat imports: from backend import constants (works via re-exports below)
    
    This allows existing code using the flat structure to continue working
    while new code can use the hierarchical package imports.

Architecture Benefits:
    - Clear separation of concerns
    - Reduced circular dependencies
    - Easier testing and maintenance
    - Better IDE code navigation
    - Scalable for future expansion

Legacy Import Paths (still supported):
    from backend import constants         # → backend.core.constants
    from backend import exceptions        # → backend.core.exceptions
    from backend import gameobject        # → backend.core.gameobject
    from backend import engine_utils      # → backend.core.engine_utils
    from backend import data              # → backend.systems.data
    from backend import effects           # → backend.systems.effects
    from backend import job_requirements  # → backend.systems.job_requirements
    from backend import job               # → backend.systems.job
    from backend import game_utils        # → backend.systems.game_utils
    from backend import building          # → backend.entities.building
    from backend import city              # → backend.entities.city
    from backend import empire            # → backend.entities.empire
    from backend import unit              # → backend.entities.unit
    from backend import army              # → backend.entities.army
    from backend import ideology          # → backend.entities.ideology
    from backend import game              # → backend.gameplay.game
    from backend import location          # → backend.gameplay.location
    from backend import events            # → backend.gameplay.events
"""

# ============================================================================
# Core Package Re-exports
# ============================================================================
from .core import (
    constants,
    exceptions,
    gameobject,
    engine_utils,
)

# ============================================================================
# Systems Package Re-exports
# ============================================================================
from .systems import (
    data,
    effects,
    job_requirements,
    job,
    game_utils,
)

# ============================================================================
# Entities Package Re-exports
# ============================================================================
from .entities import (
    building,
    city,
    empire,
    unit,
    army,
    ideology,
)

# ============================================================================
# Gameplay Package Re-exports
# ============================================================================
from .gameplay import (
    game,
    location,
    events,
)

# ============================================================================
# Direct Class Re-exports (for convenience)
# ============================================================================
# Core classes
from .core.constants import *
from .core.exceptions import *
from .core.gameobject import GameObject
from .core.engine_utils import *

# Systems classes
from .systems.data import (
    ExpendableCityResources,
    ExpendableEmpireResources,
)
from .systems.effects import Effect
from .systems.job_requirements import JobRequirements
from .systems.job import Job, DestructionJob
from .systems.game_utils import new_value_given_morale

# Entities classes
from .entities.building import Building
from .entities.city import City
from .entities.empire import Empire, EmptyEmpire
from .entities.unit import Unit
from .entities.army import Army
from .entities.ideology import Ideology

# Gameplay classes
from .gameplay.game import Game, EmptyGame
from .gameplay.location import GameNode, Path, PathDirection, WorldMap
from .gameplay.events import GameEvent, EventType

# ============================================================================
# Module-level __all__ for explicit exports
# ============================================================================
__all__ = [
    # Modules (for from backend import X style)
    "constants",
    "exceptions",
    "gameobject",
    "engine_utils",
    "data",
    "effects",
    "job_requirements",
    "job",
    "game_utils",
    "building",
    "city",
    "empire",
    "unit",
    "army",
    "ideology",
    "game",
    "location",
    "events",
    # Direct classes (frequently used)
    "GameObject",
    "Effect",
    "Job",
    "DestructionJob",
    "Building",
    "City",
    "Empire",
    "EmptyEmpire",
    "Unit",
    "Army",
    "Ideology",
    "Game",
    "EmptyGame",
    "GameNode",
    "Path",
    "PathDirection",
    "WorldMap",
    "GameEvent",
    "EventType",
    "ExpendableCityResources",
    "ExpendableEmpireResources",
    "JobRequirements",
    "new_value_given_morale",
]