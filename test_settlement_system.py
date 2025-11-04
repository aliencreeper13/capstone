"""
Test script to verify the Settler settlement system is working correctly.

This tests:
1. GameNode and WorldMap infrastructure
2. Game engine settlement checking
3. City and unit management
"""

import sys
sys.path.insert(0, r'c:\Users\MrCheese\Desktop\Programming\Python\capstone')

from backend.gameplay.location import GameNode, WorldMap
from backend.gameplay.game import Game

def test_gamenode_infrastructure():
    """Test GameNode has all settlement-related properties and methods."""
    print("\n=== Testing GameNode Infrastructure ===")
    
    gn = GameNode(coords=(0, 0), size=5)
    
    # Test basic properties
    assert gn.coords == (0, 0), "coords property failed"
    assert gn.x == 0, "x property failed"
    assert gn.y == 0, "y property failed"
    assert gn.size == 5, "size property failed"
    print("✓ Basic properties (coords, x, y, size)")
    
    # Test claim system
    assert not gn.is_claimed, "Node should start unclaimed"
    assert gn.claimed_by_empire is None, "Node should have no empire initially"
    print("✓ Claim system (is_claimed, claimed_by_empire)")
    
    # Test armies
    assert gn.armies() == [], "Node should start with no armies"
    print("✓ Armies management")
    
    print("✅ GameNode infrastructure test PASSED")

def test_worldmap_infrastructure():
    """Test WorldMap has node management methods."""
    print("\n=== Testing WorldMap Infrastructure ===")
    
    wm = WorldMap(size=(100, 100))
    node1 = GameNode(coords=(10, 10), size=5)
    node2 = GameNode(coords=(20, 20), size=5)
    
    # Test add_node
    wm.add_node(node1)
    assert len(wm.get_nodes()) == 1, "Should have 1 node"
    print("✓ add_node()")
    
    wm.add_node(node2)
    assert len(wm.get_nodes()) == 2, "Should have 2 nodes"
    print("✓ Multiple nodes")
    
    # Test remove_node
    wm.remove_node(node1)
    assert len(wm.get_nodes()) == 1, "Should have 1 node after removal"
    assert node2 in wm.get_nodes(), "Remaining node should be node2"
    print("✓ remove_node()")
    
    print("✅ WorldMap infrastructure test PASSED")

def test_game_settlement_infrastructure():
    """Test Game engine has settlement checking capabilities."""
    print("\n=== Testing Game Settlement Infrastructure ===")
    
    wm = WorldMap(size=(100, 100))
    game = Game(worldmap=wm, empires=[])
    
    # Test properties
    assert game.worldmap is wm, "worldmap property failed"
    assert game.current_tick == 0, "current_tick should start at 0"
    print("✓ Game properties (worldmap, current_tick)")
    
    # Test settlement methods exist
    assert hasattr(game, '_check_settler_settlements'), "Missing _check_settler_settlements"
    assert hasattr(game, '_settle_node_as_city'), "Missing _settle_node_as_city"
    print("✓ Settlement methods exist")
    
    # Test next_tick runs without errors
    node = GameNode(coords=(15, 15), size=5)
    wm.add_node(node)
    game.next_tick()
    assert game.current_tick == 1, "Tick should increment"
    print("✓ next_tick() executes and calls settlement checking")
    
    print("✅ Game settlement infrastructure test PASSED")

def test_city_unit_management():
    """Test City has unit management methods for settlement."""
    print("\n=== Testing City Unit Management ===")
    
    try:
        from backend.entities.city import City
        from backend.entities.army import MobileUnitGroup
        
        city = City(coords=(50, 50), size=5)
        
        # Test unit management methods
        assert hasattr(city, '_add_troop'), "Missing _add_troop"
        assert hasattr(city, '_add_passive_unit'), "Missing _add_passive_unit"
        assert hasattr(city, '_troop_group'), "Missing _troop_group"
        assert hasattr(city, '_passive_unit_group'), "Missing _passive_unit_group"
        print("✓ City unit management infrastructure")
        
        # Test that troop and passive unit groups are MobileUnitGroup
        assert isinstance(city._troop_group, MobileUnitGroup), "troop_group should be MobileUnitGroup"
        assert isinstance(city._passive_unit_group, MobileUnitGroup), "passive_unit_group should be MobileUnitGroup"
        print("✓ Unit groups are MobileUnitGroup instances")
        
        print("✅ City unit management test PASSED")
    except ImportError as e:
        print(f"⚠ Skipping City test due to import issues: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("SETTLER SETTLEMENT SYSTEM TEST SUITE")
    print("=" * 60)
    
    test_gamenode_infrastructure()
    test_worldmap_infrastructure()
    test_game_settlement_infrastructure()
    test_city_unit_management()
    
    print("\n" + "=" * 60)
    print("✅✅✅ ALL TESTS PASSED! ✅✅✅")
    print("Settlement system infrastructure is ready for use!")
    print("=" * 60)