"""
Quick test to verify interactive demo can initialize properly.
"""

import sys
sys.path.insert(0, r'c:\Users\MrCheese\Desktop\Programming\Python\capstone')

from interactive_demo import create_game

print("=" * 70)
print("INTERACTIVE DEMO - INITIALIZATION TEST")
print("=" * 70)

try:
    print("\n[*] Creating game with default settings...")
    game, empire, city = create_game("Test Empire", "Test City", "Republic")
    
    print("\n[*] Assigning names...")
    empire.name = "Test Empire"
    city.name = "Test City"
    
    print("\n[*] Running 5 game ticks...")
    for i in range(5):
        game.next_tick()
        print(f"    Tick {game.current_tick}: Population={city.total_population}, "
              f"Food={city._resources.food:.1f}, Wealth={city._resources.wealth:.1f}, "
              f"Morale={city.morale:.1f}")
    
    print("\n" + "=" * 70)
    print("✅ INITIALIZATION TEST PASSED")
    print("=" * 70)
    print("\nYou can now run: python interactive_demo.py")
    print("to start the interactive game!")
    
except Exception as e:
    print(f"\n[!] ERROR: {e}")
    import traceback
    traceback.print_exc()