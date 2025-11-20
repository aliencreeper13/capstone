"""
Test suite for path intersection prevention in WorldMap generation.

This test verifies that paths created during map generation do not intersect
with each other, ensuring a clean and visually clear map layout.
"""

import sys
from pathlib import Path

# Add capstone root to path for imports
capstone_root = Path(__file__).parent
sys.path.insert(0, str(capstone_root))

from backend.gameplay.location import WorldMap, GameNode


def test_segment_intersection_basic():
    """Test basic line segment intersection detection."""
    # Test case 1: Intersecting segments (X pattern)
    p1, p2 = (0, 0), (2, 2)
    p3, p4 = (0, 2), (2, 0)
    assert WorldMap._segments_intersect(p1, p2, p3, p4), "Should detect X-pattern intersection"
    print("✓ Test 1: X-pattern intersection detected")
    
    # Test case 2: Non-intersecting segments (parallel)
    p1, p2 = (0, 0), (2, 0)
    p3, p4 = (0, 1), (2, 1)
    assert not WorldMap._segments_intersect(p1, p2, p3, p4), "Should not detect parallel segments as intersecting"
    print("✓ Test 2: Parallel segments correctly identified as non-intersecting")
    
    # Test case 3: Segments sharing endpoint (should NOT count as intersection)
    p1, p2 = (0, 0), (2, 0)
    p3, p4 = (2, 0), (2, 2)
    assert not WorldMap._segments_intersect(p1, p2, p3, p4), "Segments sharing endpoint should not be considered intersecting"
    print("✓ Test 3: Shared endpoints correctly handled")
    
    # Test case 4: Touching end of segment (should NOT count as intersection)
    p1, p2 = (0, 0), (2, 2)
    p3, p4 = (1, 1), (3, 1)
    # This touches at the midpoint, should not intersect
    result = WorldMap._segments_intersect(p1, p2, p3, p4)
    print(f"✓ Test 4: Touching segments test completed (result: {result})")


def test_segment_intersection_edge_cases():
    """Test edge cases for line segment intersection."""
    # Test case 1: T-shaped intersection
    p1, p2 = (0, 0), (2, 0)
    p3, p4 = (1, -1), (1, 1)
    result = WorldMap._segments_intersect(p1, p2, p3, p4)
    assert result, "Should detect T-shaped intersection"
    print("✓ Test 5: T-shaped intersection detected")
    
    # Test case 2: Segments that don't intersect but would if extended
    p1, p2 = (0, 0), (1, 1)
    p3, p4 = (2, 0), (3, 1)
    assert not WorldMap._segments_intersect(p1, p2, p3, p4), "Should not intersect when not extended"
    print("✓ Test 6: Non-intersecting adjacent segments correctly identified")


def test_no_path_intersection_small_map():
    """Test that paths don't intersect in a small generated map."""
    print("\nGenerating small map (4 nodes)...")
    world = WorldMap.generate_random_map(
        size=(500, 500),
        num_nodes=4,
        min_distance_between_nodes=50,
        node_sizes=15
    )
    
    paths = world.get_paths()
    print(f"Generated {len(paths)} paths")
    
    # Check for intersections
    path_list = list(paths.keys())
    intersections_found = 0
    
    for i, (node1_a, node2_a) in enumerate(path_list):
        for j, (node1_b, node2_b) in enumerate(path_list):
            if i >= j:  # Skip self and duplicate checks
                continue
            
            if WorldMap._segments_intersect(
                node1_a.coords, node2_a.coords,
                node1_b.coords, node2_b.coords
            ):
                intersections_found += 1
                print(f"  ✗ Path intersection found: "
                      f"({node1_a.x},{node1_a.y})-({node2_a.x},{node2_a.y}) crosses "
                      f"({node1_b.x},{node1_b.y})-({node2_b.x},{node2_b.y})")
    
    assert intersections_found == 0, f"Found {intersections_found} path intersections!"
    print("✓ Test 7: No path intersections in 4-node map")


def test_no_path_intersection_medium_map():
    """Test that paths don't intersect in a medium-sized generated map."""
    print("\nGenerating medium map (8 nodes)...")
    world = WorldMap.generate_random_map(
        size=(1000, 1000),
        num_nodes=8,
        min_distance_between_nodes=80,
        node_sizes=20
    )
    
    paths = world.get_paths()
    print(f"Generated {len(paths)} paths")
    
    # Check for intersections
    path_list = list(paths.keys())
    intersections_found = 0
    
    for i, (node1_a, node2_a) in enumerate(path_list):
        for j, (node1_b, node2_b) in enumerate(path_list):
            if i >= j:  # Skip self and duplicate checks
                continue
            
            if WorldMap._segments_intersect(
                node1_a.coords, node2_a.coords,
                node1_b.coords, node2_b.coords
            ):
                intersections_found += 1
    
    assert intersections_found == 0, f"Found {intersections_found} path intersections!"
    print("✓ Test 8: No path intersections in 8-node map")


def test_no_path_intersection_large_map():
    """Test that paths don't intersect in a larger map."""
    print("\nGenerating larger map (12 nodes)...")
    world = WorldMap.generate_random_map(
        size=(1500, 1500),
        num_nodes=12,
        min_distance_between_nodes=100,
        node_sizes=25
    )
    
    paths = world.get_paths()
    print(f"Generated {len(paths)} paths")
    
    # Check for intersections
    path_list = list(paths.keys())
    intersections_found = 0
    
    for i, (node1_a, node2_a) in enumerate(path_list):
        for j, (node1_b, node2_b) in enumerate(path_list):
            if i >= j:  # Skip self and duplicate checks
                continue
            
            if WorldMap._segments_intersect(
                node1_a.coords, node2_a.coords,
                node1_b.coords, node2_b.coords
            ):
                intersections_found += 1
    
    assert intersections_found == 0, f"Found {intersections_found} path intersections!"
    print("✓ Test 9: No path intersections in 12-node map")


def test_paths_still_connect():
    """Verify that nodes are still well-connected despite intersection prevention."""
    print("\nVerifying connectivity with intersection prevention...")
    world = WorldMap.generate_random_map(
        size=(800, 800),
        num_nodes=6,
        min_distance_between_nodes=60,
        node_sizes=15
    )
    
    nodes = world.get_nodes()
    paths = world.get_paths()
    
    print(f"Nodes: {len(nodes)}, Paths: {len(paths)}")
    
    # Check that most nodes have at least one connection
    connected_nodes = set()
    for (node1, node2) in paths.keys():
        connected_nodes.add(node1)
        connected_nodes.add(node2)
    
    connection_rate = len(connected_nodes) / len(nodes) * 100
    print(f"Connected nodes: {len(connected_nodes)}/{len(nodes)} ({connection_rate:.1f}%)")
    
    # With 6 nodes, at least 5 should be connected (95% or more)
    assert connection_rate >= 95, f"Too few nodes connected: {connection_rate:.1f}%"
    print("✓ Test 10: Nodes remain well-connected despite intersection prevention")


def run_all_tests():
    """Run all path intersection tests."""
    print("=" * 60)
    print("Path Intersection Prevention Test Suite")
    print("=" * 60)
    
    try:
        test_segment_intersection_basic()
        test_segment_intersection_edge_cases()
        test_no_path_intersection_small_map()
        test_no_path_intersection_medium_map()
        test_no_path_intersection_large_map()
        test_paths_still_connect()
        
        print("\n" + "=" * 60)
        print("✅ All Tests Passed!")
        print("=" * 60)
        return True
    except AssertionError as e:
        print(f"\n❌ Test Failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)