#!/usr/bin/env python3
"""
Game Launcher Script - Run the civilization game engine.

This wrapper script properly configures the Python path and runs the game.
Usage: python run_game.py

Note: This script should be run from the capstone directory (where this file is located).
"""

import sys
import os

# Add the capstone directory to the Python path so backend can be imported as a package
capstone_dir = os.path.dirname(os.path.abspath(__file__))
if capstone_dir not in sys.path:
    sys.path.insert(0, capstone_dir)

# Now we can import and run the game
from backend.main import create_demo_game, run_demo_game

if __name__ == "__main__":
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
        print(f"\n❌ Error during game: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)