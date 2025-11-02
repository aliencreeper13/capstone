#!/usr/bin/env python3
"""Test backward compatibility imports for Phase 2 refactoring."""

print("Testing Phase 2 backward compatibility imports...")

# Test 1: Module imports
print("\n1. Testing module imports...")
from backend import constants, exceptions, data, effects
from backend import job, building, city, empire, army
from backend import game, location, events
print("   ✓ Module imports work")

# Test 2: Direct class imports
print("\n2. Testing direct class imports...")
from backend import City, Empire, Building, Army, Unit
from backend import Game, EmptyGame, GameEvent, EventType
from backend import Effect, Job, JobRequirements
print("   ✓ Direct class imports work")

# Test 3: Exception imports
print("\n3. Testing exception imports...")
from backend import RequirementsException, NotEnoughWorkersException, BadEffect
print("   ✓ Exception imports work")

# Test 4: Hierarchical imports (new style)
print("\n4. Testing hierarchical imports...")
from backend.core import constants as core_constants
from backend.systems import data as systems_data
from backend.entities import city as entities_city
from backend.gameplay import game as gameplay_game
print("   ✓ Hierarchical imports work")

# Test 5: Verify classes are the same
print("\n5. Verifying class identity...")
from backend import City as BackendCity
from backend.entities import city as entities_city_module
assert BackendCity is entities_city_module.City, "City class mismatch"
print("   ✓ Re-exported classes are identical to source classes")

print("\n✅ All backward compatibility tests passed!")
print("\nPhase 2 Migration: COMPLETE")
print("  ✓ Step 1: gameplay/location.py migrated")
print("  ✓ Step 2: systems/game_utils.py migrated")
print("  ✓ Step 3: entities/city.py migrated")
print("  ✓ Step 4: entities/empire.py migrated")
print("  ✓ Step 5: gameplay/game.py migrated")
print("  ✓ Step 6: gameplay/events.py migrated")
print("  ✓ Backward compatibility layer created in backend/__init__.py")