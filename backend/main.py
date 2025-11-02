"""
Game Entry Point - Main executable for the civilization game engine.

This module provides a simple test/demo of the game engine showing:
- World map creation
- Empire and city creation
- Building and unit creation
- Basic gameplay loop

This is a command-line interface for testing the backend game logic.
Full frontend implementation will be handled separately.
"""

from __future__ import annotations

# ============================================================================
# HIERARCHICAL IMPORTS (Phase 2 Architecture)
# ============================================================================
# Note: This module should be imported via backend.main or run via run_game.py wrapper
# to ensure proper package context for relative imports

from .entities.army import ArmyAttributes, Troop
from .entities.building import Building
from .entities.ideology import Ideology
from .entities.city import City
from .entities.empire import Empire

from .systems.data import ExpendableCityResources, ExpendableEmpireResources
from .systems.effects import Effect, UniversalEffect
from .systems.job_requirements import ContingentOnInfo, JobRequirements
from .systems.job import CreationJob

from .gameplay.location import WorldMap
from .gameplay.game import Game


def create_demo_game() -> Game:
    """
    Create and initialize a demo game instance with test data.
    
    This function demonstrates how to set up a basic game with:
    - World map
    - Empires with ideologies
    - Cities with resources
    - Buildings and units
    
    Returns:
        Game: Initialized game instance ready for play
    """
    print("=" * 70)
    print("INITIALIZING GAME")
    print("=" * 70)
    
    # Create world map (1000x1000 coordinates)
    print("\n1. Creating world map...")
    worldmap = WorldMap(size=(1000, 1000))
    print("   [+] World map created (1000x1000)")
    
    # Create game instance
    print("\n2. Creating game instance...")
    game = Game(worldmap)
    print("   [+] Game instance created")
    
    # Define ideology with effects
    print("\n3. Creating ideology (Americanism)...")
    americanism = Ideology(
        effects_list=[
            UniversalEffect(
                duration_in_ticks=0,
                expendable_empire_resources_per_tick=ExpendableEmpireResources(
                    knowledge=1
                )
            )
        ],
        autonomy=50  # Medium autonomy for balanced gameplay
    )
    print("   [+] Americanism ideology created (+1 knowledge/tick)")
    
    # Create a city (capital)
    print("\n4. Creating capital city (Mequon)...")
    mequon = City((0, 0), size=50)
    mequon._resources.wealth = 100
    print("   [+] City 'Mequon' created at (0, 0)")
    print(f"      - Size: 50")
    print(f"      - Initial wealth: 100")
    
    # Create an empire
    print("\n5. Creating empire (USA)...")
    us_empire = Empire(50, capital_city=mequon, ideology=americanism)
    us_empire.add_city(mequon)
    game.add_empire(us_empire)
    print("   [+] Empire 'USA' created")
    print(f"      - Capital: Mequon")
    print(f"      - Ideology: Americanism")
    print(f"      - Cities: 1")
    
    # Define a building type
    print("\n6. Defining building type (University)...")
    
    class UniversityBuilding(Building):
        """Custom university building for demo."""
        name = "University"
        size = 5
        effect = Effect(
            duration_in_ticks=0,
            expendable_city_resources_per_tick=ExpendableCityResources(
                wealth=2
            )
        )
        job_requirements = JobRequirements(
            expendable_city_resources_level1=ExpendableCityResources(
                wealth=10
            )
        )
        description = "Educational institution producing knowledge"
    
    print("   [+] University building type defined")
    
    # Create building job
    print("\n7. Creating building job (5 ticks)...")
    university_job = CreationJob(num_ticks=5, result=UniversityBuilding)
    mequon.add_job(university_job)
    print("   [+] University construction job added")
    print(f"      - Duration: 5 ticks")
    
    # Define a unit type
    print("\n8. Defining unit type (Scholar)...")
    
    class ScholarUnit(Troop):
        """Scholar military unit for demo."""
        name = "Scholar"
        size = 1
        effect = Effect(
            expendable_empire_resources_per_tick=ExpendableEmpireResources(
                knowledge=1
            )
        )
        job_requirements = JobRequirements(
            expendable_city_resources_level1=ExpendableCityResources(
                wealth=10
            ),
            unit_types_contingent_on=[
                ContingentOnInfo(
                    unit_class=UniversityBuilding,
                    minimum_level_needed=1
                )
            ]
        )
        army_attributes = ArmyAttributes(
            hitpoints=10,
            speed=2,
            damage_per_tick=1
        )
        description = "Knowledge-producing military unit"
    
    print("   [+] Scholar unit type defined")
    
    print("\n" + "=" * 70)
    print("GAME INITIALIZATION COMPLETE")
    print("=" * 70)
    print(f"\nGame State:")
    print(f"  - Current tick: {game.current_tick}")
    print(f"  - Empires: 1")
    print(f"  - Cities: 1 (Mequon)")
    print(f"  - Building jobs queued: {len(mequon._jobs) if hasattr(mequon, '_jobs') else 0}")
    
    return game


def run_demo_game(game: Game, num_ticks: int = 10) -> None:
    """
    Run the game for a specified number of ticks.
    
    Args:
        game: The game instance to run
        num_ticks: Number of game ticks to execute (default: 10)
    """
    print("\n" + "=" * 70)
    print(f"RUNNING GAME LOOP ({num_ticks} TICKS)")
    print("=" * 70 + "\n")
    
    for i in range(num_ticks):
        game.next_tick()
        print(f"Tick {game.current_tick}: Game updated")


if __name__ == "__main__":
    """Main entry point for the game."""
    try:
        # Create and initialize the game
        game = create_demo_game()
        
        # Run the game for 10 ticks as demo
        run_demo_game(game, num_ticks=10)
        
        print("\n" + "=" * 70)
        print("DEMO COMPLETE")
        print("=" * 70)
        print("\nTo run the full game loop indefinitely, call: game.begin_game()")
        print("To run individual ticks, call: game.next_tick()")
        
    except Exception as e:
        print(f"\n[!] Error during game initialization: {e}")
        import traceback
        traceback.print_exc()