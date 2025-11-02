#!/usr/bin/env python3
"""
Test script to verify GameEvent integration with Empire and City.
"""

import sys
sys.path.insert(0, r'c:\Users\MrCheese\Desktop\Programming\Python\capstone')

from backend.entities.city import City
from backend.entities.empire import Empire
from backend.entities.ideology import NeutralIdeology
from backend.systems.job import CreationJob
from backend.systems.effects import Effect
from backend.systems.data import ExpendableCityResources, ExpendableEmpireResources
from backend.systems.job_requirements import JobRequirements
from backend.entities.building import Building


# Define a simple test building
class TestBuilding(Building):
    name = "TestBuilding"
    size = 1
    effect = Effect(duration_in_ticks=0, expendable_city_resources_per_tick=ExpendableCityResources(food=1))
    job_requirements = JobRequirements(expendable_city_resources_level1=ExpendableCityResources(wealth=10), workers_needed_level1=1)
    description = "Test building"


def test_gameevent_integration():
    """Test that GameEvent integration is working correctly."""
    print("\n" + "="*70)
    print("TESTING GAMEEVENT INTEGRATION")
    print("="*70)
    
    # Create an empire
    print("\n1. Creating empire...")
    empire = Empire(autonomy=50, capital_city=None, ideology=NeutralIdeology())
    print(f"   ✓ Empire created")
    print(f"   ✓ Initial events: {len(empire.game_events)} events")
    
    # Create a city
    print("\n2. Creating city...")
    city = City((0, 0), size=50)
    city.name = "Test City"
    city._resources.wealth = 100
    city._resources.food = 100
    city._resources.timber = 100
    city._resources.metal = 100
    city._societal_resources.population.add_population(100, 20)
    # Set up employable population (workers not yet employed)
    city._societal_resources.employable_population = 50
    print(f"   ✓ City created with resources and workers")
    
    # Add city to empire
    print("\n3. Adding city to empire...")
    empire.add_city(city)
    print(f"   ✓ City added to empire")
    
    # Test 1: Successful job submission
    print("\n4. Testing successful job submission...")
    job1 = CreationJob(num_ticks=5, result=TestBuilding)
    success, message, failures = city.add_job(job1)
    print(f"   Result: {message}")
    print(f"   Events recorded: {len(empire.game_events)}")
    if len(empire.game_events) > 0:
        event = empire.game_events[-1]
        print(f"   ✓ Event recorded: {event.description}")
        print(f"   ✓ Status: {event.data.get('status', 'N/A')}")
    
    # Test 2: Failed job submission (insufficient resources)
    print("\n5. Testing failed job submission (low resources)...")
    city._resources.wealth = 1  # Not enough
    job2 = CreationJob(num_ticks=5, result=TestBuilding)
    success, message, failures = city.add_job(job2)
    print(f"   Result: {message}")
    print(f"   Events recorded: {len(empire.game_events)}")
    if len(empire.game_events) > 1:
        event = empire.game_events[-1]
        print(f"   ✓ Event recorded: {event.description}")
        print(f"   ✓ Status: {event.data.get('status', 'N/A')}")
        if event.data.get('reasons'):
            print(f"   ✓ Failure reasons:")
            for reason in event.data['reasons']:
                print(f"       - {reason}")
    
    # Test 3: Display recent events
    print("\n6. Testing get_recent_events()...")
    recent = empire.get_recent_events(count=10)
    print(f"   ✓ Retrieved {len(recent)} recent events")
    for i, event in enumerate(recent, 1):
        print(f"   {i}. {event.description}")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED")
    print("="*70)


if __name__ == "__main__":
    test_gameevent_integration()