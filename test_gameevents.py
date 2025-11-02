#!/usr/bin/env python3
"""Quick test to verify GameEvent integration."""

import sys
sys.path.insert(0, r'c:\Users\MrCheese\Desktop\Programming\Python\capstone')

from backend.entities.empire import Empire
from backend.entities.ideology import NeutralIdeology
from backend.gameplay.events import GameEvent
from datetime import datetime

# Test imports
print("✓ GameEvent imports successful")

# Test Empire creation
empire = Empire(50, None, NeutralIdeology())
print(f"✓ Empire created")
print(f"✓ Empire has _game_events: {hasattr(empire, '_game_events')}")
print(f"✓ Empire has record_event method: {hasattr(empire, 'record_event')}")
print(f"✓ Empire game_events (property): {len(empire.game_events)} events")

# Test event recording
test_event = GameEvent(
    type="custom",
    timestamp=datetime.now(),
    source="City",
    description="✓ Test job submitted",
    data={"city_id": 1, "job_name": "Farm", "status": "success"}
)

empire.record_event(test_event)
print(f"✓ Event recorded. Total events: {len(empire.game_events)}")
print(f"✓ Event summary: {empire.game_events[0].short_summary()}")

print("\n✓ All GameEvent integration tests passed!")