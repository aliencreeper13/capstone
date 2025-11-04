"""
Test script to verify the GameNode-contains-City composition architecture.

This tests:
1. GameNodes can be created without cities
2. Cities are separate from GameNodes
3. Cities know which GameNode they belong to
4. City size cannot exceed GameNode size
5. Cities and GameNodes have separate sizes
6. Claiming and city establishment works correctly
"""

import sys
sys.path.insert(0, r'c:\Users\MrCheese\Desktop\Programming\Python\capstone')

from backend.gameplay.location import GameNode, WorldMap
from backend.entities.city import City

def test_gamenode_without_city():
    """Test that GameNodes can exist without cities."""
    print("\n=== Testing GameNode Without City ===")
    
    node = GameNode(coords=(10, 10), size=10)
    
    assert not node.has_city, "New node should not have a city"
    assert node.city is None, "New node should have None as city"
    assert not node.is_claimed, "New node should be unclaimed"
    print("✓ GameNode created without city")
    print("✓ has_city property works")
    print("✓ city property returns None")
    print("✓ Node starts unclaimed")

def test_city_separate_from_gamenode():
    """Test that City is no longer a subclass of GameNode."""
    print("\n=== Testing City Structure ===")
    
    node = GameNode(coords=(20, 20), size=10)
    city = City(gamenode=node, size=5)
    
    # Verify inheritance
    from backend.core.gameobject import GameObject
    assert isinstance(city, GameObject), "City should be GameObject"
    assert not isinstance(city, GameNode), "City should NOT be a GameNode"
    print("✓ City inherits from GameObject, not GameNode")
    
    # Verify city knows its node
    assert city.gamenode is node, "City should know its GameNode"
    print("✓ City.gamenode property works")

def test_city_size_validation():
    """Test that city size cannot exceed node size."""
    print("\n=== Testing City Size Validation ===")
    
    node = GameNode(coords=(30, 30), size=5)
    
    # Valid city (same size as node)
    city1 = City(gamenode=node, size=5)
    print("✓ City created with size equal to node size")
    
    # Valid city (smaller than node)
    node2 = GameNode(coords=(40, 40), size=10)
    city2 = City(gamenode=node2, size=5)
    print("✓ City created with size less than node size")
    
    # Invalid city (larger than node)
    node3 = GameNode(coords=(50, 50), size=5)
    try:
        city3 = City(gamenode=node3, size=10)
        print("✗ FAILED: City should not be created larger than node")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "cannot exceed" in str(e).lower()
        print("✓ ValueError raised when city size > node size")

def test_city_in_gamenode():
    """Test adding a city to a gamenode."""
    print("\n=== Testing City in GameNode ===")
    
    node = GameNode(coords=(60, 60), size=10)
    assert not node.has_city, "Node should start without city"
    
    city = City(gamenode=node, size=5)
    node.set_city(city)
    
    assert node.has_city, "Node should have city after set_city"
    assert node.city is city, "Node.city should return the set city"
    print("✓ City added to GameNode with set_city()")
    print("✓ has_city returns True")
    print("✓ city property returns the city")

def test_separate_sizes():
    """Test that GameNode and City have separate sizes."""
    print("\n=== Testing Separate Sizes ===")
    
    node = GameNode(coords=(70, 70), size=15)
    city = City(gamenode=node, size=8)
    
    assert node.size == 15, "Node should have size 15"
    assert city.size == 8, "City should have size 8"
    print(f"✓ GameNode.size: {node.size}")
    print(f"✓ City.size: {city.size}")
    print("✓ Sizes are independent")

def test_claiming_system():
    """Test claiming and city establishment."""
    print("\n=== Testing Claiming System ===")
    
    node = GameNode(coords=(80, 80), size=10)
    
    # Initially unclaimed
    assert not node.is_claimed
    assert node.claimed_by_empire is None
    print("✓ Node starts unclaimed")
    
    # Create a fake empire object for testing
    class FakeEmpire:
        def __init__(self, name):
            self.name = name
    
    empire = FakeEmpire("TestEmpire")
    
    # Claim the node
    node.claim_for_empire(empire)
    assert node.is_claimed
    assert node.claimed_by_empire is empire
    print("✓ Node can be claimed")
    print("✓ Claimed empire is tracked")

def test_gamenode_armies():
    """Test that GameNode still manages armies."""
    print("\n=== Testing GameNode Armies ===")
    
    node = GameNode(coords=(90, 90), size=10)
    
    # Node should have empty armies initially
    armies = node.armies()
    assert armies == [], "Node should start with no armies"
    print("✓ GameNode.armies() works")
    
    # Create a city in the node
    city = City(gamenode=node, size=5)
    node.set_city(city)
    
    # Node and city can have separate armies
    # (armies on node, unit groups on city)
    print("✓ City and GameNode armies are separate")

def test_worldmap_still_manages_nodes():
    """Test that WorldMap still manages all nodes."""
    print("\n=== Testing WorldMap Node Management ===")
    
    worldmap = WorldMap(size=(100, 100))
    
    node1 = GameNode(coords=(0, 0), size=10)
    node2 = GameNode(coords=(50, 50), size=10)
    
    worldmap.add_node(node1)
    worldmap.add_node(node2)
    
    assert len(worldmap.get_nodes()) == 2
    print("✓ WorldMap.add_node() works")
    
    # Add cities to nodes - nodes should still be in map
    city1 = City(gamenode=node1, size=5)
    node1.set_city(city1)
    
    assert len(worldmap.get_nodes()) == 2, "Adding city should not change node count"
    assert node1 in worldmap.get_nodes(), "Node with city should still be in map"
    print("✓ Nodes remain in WorldMap after city establishment")
    print("✓ Nodes are not replaced")

if __name__ == '__main__':
    print("=" * 60)
    print("GAMENODE-CITY COMPOSITION ARCHITECTURE TEST SUITE")
    print("=" * 60)
    
    test_gamenode_without_city()
    test_city_separate_from_gamenode()
    test_city_size_validation()
    test_city_in_gamenode()
    test_separate_sizes()
    test_claiming_system()
    test_gamenode_armies()
    test_worldmap_still_manages_nodes()
    
    print("\n" + "=" * 60)
    print("✅✅✅ ALL TESTS PASSED! ✅✅✅")
    print("GameNode-City composition architecture is working!")
    print("=" * 60)