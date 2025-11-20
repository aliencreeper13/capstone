"""
Interactive Demo Game - A simple terminal-based civilization game.

Features:
- Single empire with one capital city
- Interactive commands for viewing stats and managing the city
- Building construction with resource requirements
- Dynamic effects system with contingencies
- Real-time gameplay with 1-second ticks

Usage:
    python interactive_demo.py
"""

import sys
import time
import threading
from typing import Optional

sys.path.insert(0, r'c:\Users\MrCheese\Desktop\Programming\Python\capstone')

from backend.entities.city import City
from backend.entities.empire import Empire
from backend.entities.ideology import (
    NeutralIdeology, Monarchy, Republic, Communism,
    Dictatorship, Anarchy, Socialism, Theocracy
)
from backend.entities.building import Building
from backend.gameplay.location import WorldMap, GameNode
from backend.gameplay.game import Game
from backend.gameplay.events import GameEvent
from backend.systems.data import ExpendableCityResources, ExpendableEmpireResources
from backend.systems.job import CreationJob
from backend.systems.effects import Effect
from backend.systems.job_requirements import JobRequirements


# ============================================================================
# BUILDING DEFINITIONS
# ============================================================================
from backend.unit_classes.buildings import *

# ============================================================================
# GAME SETUP
# ============================================================================

def get_empire_setup() -> tuple[str, str, str]:
    """
    Prompt player for empire name, capital city name, and ideology choice.
    
    Returns:
        Tuple of (empire_name, city_name, ideology_choice)
    """
    print("\n" + "=" * 70)
    print("WELCOME TO THE CIVILIZATION EMPIRE BUILDER DEMO")
    print("=" * 70)
    
    # Get empire name
    while True:
        empire_name = input("\nEnter your empire name: ").strip()
        if empire_name and len(empire_name) <= 50:
            break
        print("  [!] Please enter a valid name (1-50 characters)")
    
    # Get capital city name
    while True:
        city_name = input("Enter your capital city name: ").strip()
        if city_name and len(city_name) <= 50:
            break
        print("  [!] Please enter a valid name (1-50 characters)")
    
    # Get ideology choice
    ideologies = {
        "1": ("Neutral", NeutralIdeology),
        "2": ("Monarchy", Monarchy),
        "3": ("Republic", Republic),
        "4": ("Communism", Communism),
        "5": ("Dictatorship", Dictatorship),
        "6": ("Anarchy", Anarchy),
        "7": ("Socialism", Socialism),
        "8": ("Theocracy", Theocracy),
    }
    
    print("\nChoose your ideology:")
    for key, (name, _) in ideologies.items():
        print(f"  {key}. {name}")
    
    while True:
        choice = input("\nEnter ideology number (1-8): ").strip()
        if choice in ideologies:
            ideology_name, ideology_class = ideologies[choice]
            break
        print("  [!] Please enter a number between 1 and 8")
    
    return empire_name, city_name, ideology_name


def create_game(empire_name: str, city_name: str, ideology_choice: str) -> tuple[Game, Empire, City]:
    """
    Create and initialize the game with the specified parameters.
    
    Args:
        empire_name: Name of the empire
        city_name: Name of the capital city
        ideology_choice: Name of the chosen ideology
    
    Returns:
        Tuple of (game, empire, capital_city)
    """
    print("\n" + "=" * 70)
    print("INITIALIZING GAME")
    print("=" * 70)
    
    # Create world map
    print(f"\n[*] Creating world map...")
    worldmap = WorldMap(size=(100, 100))
    print(f"    ✓ World map created (100x100)")
    
    # Create game instance
    print(f"[*] Creating game instance...")
    game = Game(worldmap)
    print(f"    ✓ Game ready")
    
    # Create ideology
    print(f"[*] Creating {ideology_choice} ideology...")
    ideology_map = {
        "Neutral": NeutralIdeology(),
        "Monarchy": Monarchy(),
        "Republic": Republic(),
        "Communism": Communism(),
        "Dictatorship": Dictatorship(),
        "Anarchy": Anarchy(),
        "Socialism": Socialism(),
        "Theocracy": Theocracy(),
    }
    ideology = ideology_map[ideology_choice]
    print(f"    ✓ {ideology_choice} ideology initialized")
    
    # Create capital city
    print(f"[*] Creating capital city: {city_name}...")
    capital = City(GameNode((0, 0), size=50), size=50)
    capital._resources.wealth = 50
    capital._resources.food = 50
    capital._resources.timber = 30
    capital._resources.metal = 20
    capital._societal_resources.population.add_population(200, 20)
    print(f"    ✓ City created at (0, 0)")
    
    # Create empire
    print(f"[*] Creating empire: {empire_name}...")
    empire = Empire(autonomy=50, capital_city=capital, ideology=ideology)
    empire.add_city(capital)
    
    game.add_empire(empire)
    print(f"    ✓ Empire established")
    
    print("\n" + "=" * 70)
    print("GAME INITIALIZED SUCCESSFULLY")
    print("=" * 70)
    
    return game, empire, capital


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def clear_screen():
    """Clear the terminal screen."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def display_status(city: City, empire: Empire, tick: int):
    """Display the current game status."""
    print("\n" + "=" * 70)
    print(f"GAME STATUS - TICK {tick}")
    print("=" * 70)
    
    # Empire stats
    empire_name = getattr(empire, 'name', 'Unknown Empire')
    print(f"\n[EMPIRE] {empire_name}")
    print(f"  Knowledge: {empire.knowledge:.0f}")
    print(f"  Efficiency: {empire.efficiency:.1f}% (Corruption: {100 - empire.efficiency:.1f}%)")
    
    # City stats
    city_name = getattr(city, 'name', 'Capital')
    print(f"\n[CITY] {city_name}")
    print(f"  Population: {city.total_population}")
    print(f"  Employable population: {city.employable_population}")
    print(f"  Morale: {city.morale:.1f}/100")
    try:
        space_used = sum(b.size for b in city._buildings) if city._buildings else 0
        space_left = city.size - space_used
        print(f"  Size: {space_used}/{city.size} ({space_left} free)")
    except:
        print(f"  Size: {city.size} total")
    
    # Resources
    print(f"\n[RESOURCES]")
    print(f"  Food:   {city._resources.food:>6.1f} / {city.expendable_resource_capacities.food:>6.1f}")
    print(f"  Timber: {city._resources.timber:>6.1f} / {city.expendable_resource_capacities.timber:>6.1f}")
    print(f"  Metal:  {city._resources.metal:>6.1f} / {city.expendable_resource_capacities.metal:>6.1f}")
    print(f"  Wealth: {city._resources.wealth:>6.1f} / {city.expendable_resource_capacities.wealth:>6.1f}")
    
    # Buildings
    if city._buildings:
        print(f"\n[BUILDINGS] ({len(city._buildings)} total)")
        building_counts = {}
        for building in city._buildings:
            name = building.__class__.__name__
            building_counts[name] = building_counts.get(name, 0) + 1
        for name, count in sorted(building_counts.items()):
            print(f"  {name}: {count}")
    else:
        print(f"\n[BUILDINGS] None")
    
    # Active jobs
    if city._running_jobs:
        print(f"\n[CONSTRUCTION JOBS] ({len(city._running_jobs)} active)")
        for i, job in enumerate(city._running_jobs, 1):
            if hasattr(job, 'result'):
                job_name = job.result.__name__ if hasattr(job.result, '__name__') else str(job.result)
                progress = f"{job.progress}/{job.num_ticks}" if hasattr(job, 'progress') else "..."
                print(f"  {i}. {job_name} ({progress})")
    else:
        print(f"\n[CONSTRUCTION JOBS] None")


def display_building_options():
    """Display available buildings to construct."""
    buildings = [
        ("1", "Farm", Farm),
        ("2", "Market", Market),
        ("3", "School", School),
        ("4", "WoodcuttersCamp", WoodcuttersCamp),
        ("5", "Mine", Mine),
        ("6", "Library", Library),
        ("7", "Temple", Temple),
        ("8", "Housing", Housing),
        ("9", "Granary", Granary),
        ("10", "LumberYard", LumberYard),
        ("11", "University", University),
        ("12", "Hospital", Hospital),
    ]
    
    print("\nAvailable Buildings to Construct:")
    for key, display_name, building_class in buildings:
        req = building_class.job_requirements
        print(f"\n  {key}. {building_class.name}")
        print(f"     Size: {building_class.size}, Effect: {building_class.description}")
        print(f"     Cost: W={req.expendable_city_resources_level1.wealth}, "
              f"T={req.expendable_city_resources_level1.timber}, "
              f"M={req.expendable_city_resources_level1.metal}, "
              f"F={req.expendable_city_resources_level1.food}")
    
    return buildings


def display_help():
    """Display available commands."""
    print("\nAvailable Commands:")
    print("  status   - View current game status")
    print("  build    - Start building a new structure")
    print("  jobs     - View active construction jobs")
    print("  events   - View recent game events")
    print("  help     - Show this help message")
    print("  next     - Advance time by 1 tick (1 second)")
    print("  auto N   - Auto-advance N ticks (default 10)")
    print("  quit     - Exit the game")


def display_events(empire: Empire, count: int = 10):
    """
    Display recent game events for the empire.
    
    Args:
        empire: The empire to display events for
        count: Number of recent events to display (default 10)
    """
    events = empire.game_events
    if not events:
        print("\nNo recent events.")
        return
    
    # Show the most recent N events
    recent = list(reversed(events[-count:]))
    
    print(f"\n{'='*70}")
    print(f"RECENT GAME EVENTS (showing {len(recent)} of {len(events)} total)")
    print(f"{'='*70}")
    
    for i, event in enumerate(recent, 1):
        timestamp = event.timestamp.strftime("%H:%M:%S") if hasattr(event.timestamp, 'strftime') else str(event.timestamp)
        print(f"\n  {i}. [{timestamp}] {event.description}")
        
        # Show additional details if available
        if event.data:
            if "status" in event.data:
                status_display = "✓" if event.data["status"] == "started" else "✗"
                print(f"     Status: {status_display} {event.data['status'].upper()}")
            
            if "reasons" in event.data and event.data["reasons"]:
                print(f"     Failures:")
                for reason in event.data["reasons"]:
                    print(f"       - {reason}")


# ============================================================================
# GAME LOOP
# ============================================================================

class InteractiveGame:
    """Main interactive game controller."""
    
    def __init__(self, game: Game, empire: Empire, city: City):
        self.game = game
        self.empire = empire
        self.city = city
        self.running = True
        self.auto_advance = 0
        self.last_tick = 0
        
    def process_command(self, command: str):
        """Process player command."""
        command = command.strip().lower()
        
        if command == "status":
            display_status(self.city, self.empire, self.game.current_tick)
        
        elif command == "build":
            self.handle_build()
        
        elif command == "jobs":
            if self.city._running_jobs:
                print(f"\nActive Jobs: {len(self.city._running_jobs)}")
                for i, job in enumerate(self.city._running_jobs, 1):
                    job_name = job.result.__name__ if hasattr(job.result, '__name__') else str(job.result)
                    progress = f"{job.progress}/{job.num_ticks}" if hasattr(job, 'progress') else "..."
                    print(f"  {i}. {job_name} ({progress})")
            else:
                print("\nNo active construction jobs.")
        
        elif command == "events":
            display_events(self.empire)
        
        elif command == "next":
            self.advance_tick()
        
        elif command.startswith("auto"):
            parts = command.split()
            try:
                ticks = int(parts[1]) if len(parts) > 1 else 10
                self.auto_advance = ticks
                print(f"\nAuto-advancing {ticks} ticks...")
            except ValueError:
                print("[!] Please enter a valid number")
        
        elif command == "help":
            display_help()
        
        elif command == "quit":
            print("\nThanks for playing! Goodbye!")
            self.running = False
        
        else:
            print(f"[!] Unknown command: {command}")
            print("    Type 'help' for available commands")
    
    def handle_build(self):
        """Handle building construction."""
        buildings = display_building_options()
        
        while True:
            choice = input("\nEnter building number (or 'q' to cancel): ").strip()
            
            if choice.lower() == 'q':
                return
            
            # Find the selected building
            building = None
            for key, name, building_class in buildings:
                if key == choice:
                    building = building_class
                    break
            
            if building is None:
                print("[!] Invalid building number")
                continue
            
            # Check space (not part of job requirements)
            if self.city.space_left < building.size:
                print(f"[!] Not enough space! Need {building.size}, have {self.city.space_left}")
                continue
            
            # Get cost for display
            cost = building.job_requirements.expendable_city_resources_level1
            
            # Start construction
            try:
                job = CreationJob(result=building)
                success, message, failures = self.city.add_job(job)
                
                # Display result with formatted message
                print(f"\n{message}")
                
                if not success:
                    # Show detailed failure reasons
                    if failures:
                        print("  Reasons:")
                        for reason in failures:
                            print(f"    - {reason}")
                else:
                    # Job started successfully, show resource consumption
                    duration = building.job_num_ticks
                    print(f"  Duration: {duration} ticks")
                    print(f"  Resources consumed: W={cost.wealth:.1f}, T={cost.timber:.1f}, M={cost.metal:.1f}, F={cost.food:.1f}")
                
                return
            except Exception as e:
                print(f"[!] Error starting construction: {e}")
                return
    
    def advance_tick(self):
        """Advance game by one tick (1 second)."""
        try:
            self.game.next_tick()
            print(f"\n[+] Game advanced to tick {self.game.current_tick}")
        except Exception as e:
            print(f"[!] Error advancing game: {e}")
    
    def run(self):
        """Main game loop."""
        display_status(self.city, self.empire, self.game.current_tick)
        display_help()
        
        while self.running:
            try:
                if self.auto_advance > 0:
                    self.advance_tick()
                    self.auto_advance -= 1
                    if self.auto_advance == 0:
                        display_status(self.city, self.empire, self.game.current_tick)
                    time.sleep(1)
                else:
                    command = input("\n> ").strip()
                    if command:
                        self.process_command(command)
            
            except KeyboardInterrupt:
                print("\n\nGame interrupted by user.")
                self.running = False
            except Exception as e:
                print(f"\n[!] Error: {e}")
                import traceback
                traceback.print_exc()


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    try:
        # Get player setup
        empire_name, city_name, ideology_choice = get_empire_setup()
        
        # Create game
        game, empire, city = create_game(empire_name, city_name, ideology_choice)
        
        # Store names for display
        empire.name = empire_name
        city.name = city_name
        
        # Run interactive game
        interactive_game = InteractiveGame(game, empire, city)
        interactive_game.run()
        
        print("\n" + "=" * 70)
        print("GAME ENDED")
        print("=" * 70)
    
    except Exception as e:
        print(f"\n[!] Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()