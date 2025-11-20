"""
Generate and visualize a WorldMap with non-intersecting paths.

This script creates example maps showing how the path intersection
prevention produces clean, non-crossing road networks.
"""

import sys
from pathlib import Path

# Add capstone root to path for imports
capstone_root = Path(__file__).parent
sys.path.insert(0, str(capstone_root))

from backend.gameplay.location import WorldMap


def main():
    print("=" * 60)
    print("WorldMap Visualization - Non-Intersecting Paths")
    print("=" * 60)
    
    # Example 1: Small map (4 nodes)
    print("\n1. Generating small map (4 nodes)...")
    try:
        world1 = WorldMap.generate_random_map(
            size=(600, 600),
            num_nodes=4,
            min_distance_between_nodes=80,
            node_sizes=20
        )
        world1.visualize("test_map_no_intersect_small.png", scale=1.0)
        print("   ✓ Saved: test_map_no_intersect_small.png")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Example 2: Medium map (8 nodes)
    print("\n2. Generating medium map (8 nodes)...")
    try:
        world2 = WorldMap.generate_random_map(
            size=(1000, 1000),
            num_nodes=8,
            min_distance_between_nodes=80,
            node_sizes=20
        )
        world2.visualize("test_map_no_intersect_medium.png", scale=1.0)
        print("   ✓ Saved: test_map_no_intersect_medium.png")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Example 3: Larger map (12 nodes)
    print("\n3. Generating larger map (12 nodes)...")
    try:
        world3 = WorldMap.generate_random_map(
            size=(1500, 1500),
            num_nodes=12,
            min_distance_between_nodes=100,
            node_sizes=25
        )
        world3.visualize("test_map_no_intersect_large.png", scale=1.0)
        print("   ✓ Saved: test_map_no_intersect_large.png")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Example 4: Scaled visualization of medium map
    print("\n4. Generating scaled visualization (2x scale)...")
    try:
        world2.visualize("test_map_no_intersect_medium_2x.png", scale=2.0)
        print("   ✓ Saved: test_map_no_intersect_medium_2x.png (2x scale)")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Visualization complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()