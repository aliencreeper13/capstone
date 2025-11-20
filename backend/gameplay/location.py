"""
Location and path management for the game world.

This module defines the spatial structure of the game world:
- GameNode: A location on the map (city location or strategic point)
- Path: A connection between two GameNodes for army movement
- PathDirection: Directional enum for path traversal
- WorldMap: The overall map structure (placeholder for future expansion)

Armies move along paths between game nodes, with their position tracked as a
floating-point value between 0 (at starting node) and distance (at ending node).
"""

from __future__ import annotations

from enum import Enum
from math import sqrt
import math
import random
from typing import TYPE_CHECKING, Optional
from pathlib import Path as PathlibPath

from ..core.exceptions import BadGameNodeException
from ..core.gameobject import GameObject

if TYPE_CHECKING:
    from ..entities.army import Army, Troop
    from ..entities.empire import Empire
    from ..entities.city import City

try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class PathDirection(Enum):
    """Direction of movement along a path."""
    FORWARDS = +1
    BACKWARDS = -1


class WorldMap(GameObject):
    """
    Represents the overall game map structure.
    
    Manages:
    - All game nodes on the map (each node may or may not contain a city)
    - All paths between nodes
    - Map size and terrain
    """
    
    def __init__(self, size: tuple[int, int]):
        """
        Initialize a new world map.
        
        Args:
            size: (width, height) of the map in units
        """
        super().__init__()
        self._size: tuple[int, int] = size
        self._nodes: list[GameNode] = []
        self._paths: dict[tuple[GameNode, GameNode], Path] = {}
    
    @staticmethod
    def _ccw(A: tuple[float, float], B: tuple[float, float], C: tuple[float, float]) -> bool:
        """
        Counter-clockwise orientation test for three points.
        Used in line segment intersection detection.
        
        Args:
            A, B, C: Points as (x, y) tuples
            
        Returns:
            True if points are in counter-clockwise order
        """
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
    
    @staticmethod
    def _segments_intersect(
        p1: tuple[float, float], 
        p2: tuple[float, float], 
        p3: tuple[float, float], 
        p4: tuple[float, float]
    ) -> bool:
        """
        Check if line segment p1-p2 intersects with line segment p3-p4.
        
        Uses the counter-clockwise orientation method. Returns True if segments
        intersect (including touching at endpoints).
        
        Args:
            p1, p2: Endpoints of first segment
            p3, p4: Endpoints of second segment
            
        Returns:
            True if segments intersect
        """
        # Check if segments share an endpoint (not considered an intersection)
        if p1 == p3 or p1 == p4 or p2 == p3 or p2 == p4:
            return False
        
        return (
            WorldMap._ccw(p1, p3, p4) != WorldMap._ccw(p2, p3, p4) 
            and WorldMap._ccw(p1, p2, p3) != WorldMap._ccw(p1, p2, p4)
        )
    
    def add_node(self, node: GameNode) -> None:
        """
        Add a game node to the map.
        
        Args:
            node: The node to add
        """
        self._nodes.append(node)
    
    def remove_node(self, node: GameNode) -> None:
        """
        Remove a node from the map (e.g., when it becomes a City).
        
        Args:
            node: The node to remove
        """
        if node in self._nodes:
            self._nodes.remove(node)
    
    def get_nodes(self) -> list[GameNode]:
        """Get all nodes currently on the map."""
        return self._nodes

    def add_path(self, path: Path):
        """
        Add a path connecting two game nodes.
        
        Args:
            path: The path to add
        """
        key = (path._game_node1, path._game_node2)
        self._paths[key] = path
    
    def get_paths(self) -> dict[tuple[GameNode, GameNode], Path]:
        """Get all paths on the map."""
        return self._paths
    
    def visualize(self, output_path: str = "worldmap.png", scale: float = 1.0) -> None:
        """
        Create a visual representation of the world map.
        
        Creates an image with:
        - Grassy green background
        - Darker nodes representing cities/settlements
        - Brown dirt roads connecting nodes
        
        Args:
            output_path: Path where the image will be saved
            scale: Scaling factor for the map (1.0 = no scaling)
            
        Raises:
            ImportError: If PIL/Pillow is not installed
        """
        if not HAS_PIL:
            raise ImportError(
                "Pillow is required for map visualization. "
                "Install it with: pip install Pillow"
            )
        
        width, height = self._size
        scaled_width = int(width * scale)
        scaled_height = int(height * scale)
        
        # Create image with grass background (medium green)
        grass_color = (102, 153, 75)  # Medium grass green
        image = Image.new("RGB", (scaled_width, scaled_height), grass_color)
        draw = ImageDraw.Draw(image)
        
        # Draw paths first (so they're behind nodes)
        path_color = (160, 130, 80)  # Brown dirt road
        for (node1, node2) in self._paths.keys():
            x1, y1 = int(node1.x * scale), int(node1.y * scale)
            x2, y2 = int(node2.x * scale), int(node2.y * scale)
            draw.line([(x1, y1), (x2, y2)], fill=path_color, width=max(2, int(3 * scale)))
        
        # Draw nodes as circles
        node_color = (34, 102, 34)  # Darker grass green for nodes
        for node in self._nodes:
            # Calculate radius based on node size (assuming circular approximation)
            radius = max(3, int(math.sqrt(node.size / math.pi) * scale))
            x, y = int(node.x * scale), int(node.y * scale)
            
            # Draw node as filled circle
            bbox = [x - radius, y - radius, x + radius, y + radius]
            draw.ellipse(bbox, fill=node_color, outline=(0, 0, 0), width=max(1, int(scale)))
        
        # Save the image
        output_path_obj = PathlibPath(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        
        print(f"Map visualization saved to: {output_path}")

    @classmethod
    def generate_random_map(
        cls, 
        size: tuple[int, int], 
        num_nodes: int, 
        min_distance_between_nodes: int,
        node_sizes: Optional[int | list[int]] = None
    ) -> "WorldMap":
        """
        Generate a random world map of the given size.
        
        Ensures that nodes are spaced apart by at least the specified minimum distance,
        measured edge-to-edge (accounting for node sizes). Paths are created between
        nodes while preventing path-to-path intersections.
        
        Args:
            size: (width, height) of the map in units
            num_nodes: Number of nodes to generate
            min_distance_between_nodes: Minimum edge-to-edge distance between nodes
            node_sizes: Node size(s). If int, all nodes have that size. If list, must match num_nodes.
                       If None, defaults to 10 for all nodes.
        
        Returns:
            A new WorldMap with randomly placed nodes and non-intersecting paths
            connecting each node to up to 3 nearest neighbors
            
        Raises:
            ValueError: If map is too small or nodes cannot be placed without violating constraints
        """
        width, height = size
        world = cls(size)

        # Determine node sizes
        if node_sizes is None:
            node_sizes = [10] * num_nodes
        elif isinstance(node_sizes, int):
            node_sizes = [node_sizes] * num_nodes
        elif len(node_sizes) != num_nodes:
            raise ValueError(f"node_sizes list must have {num_nodes} elements, got {len(node_sizes)}")

        # --- Step 1: Feasibility Check ---
        area = width * height
        # For each node, assume circular shape with radius = sqrt(size/π)
        # Required area includes each node's area plus buffer for minimum edge distances
        radii = [math.sqrt(node_size / math.pi) for node_size in node_sizes]
        
        # Rough feasibility check: ensure total area is reasonable
        total_node_area = sum(node_sizes)
        min_required_area = total_node_area + num_nodes * (min_distance_between_nodes ** 2)
        if min_required_area > area * 2:  # 2x multiplier for reasonable spacing
            raise ValueError(
                f"World of size {size} (area={area}) is too small to fit {num_nodes} nodes "
                f"with minimum edge distance {min_distance_between_nodes}."
            )

        # --- Step 2: Generate Random, Spaced Coordinates ---
        coords_list: list[tuple[int, int]] = []
        max_attempts = 10000
        attempts = 0
        while len(coords_list) < num_nodes and attempts < max_attempts:
            x = random.randint(0, width)
            y = random.randint(0, height)
            candidate = (x, y)

            # Check distance constraint (edge-to-edge)
            valid = True
            for i, existing in enumerate(coords_list):
                # Distance between centers minus the sum of radii gives edge-to-edge distance
                center_distance = math.dist(candidate, existing)
                edge_distance = center_distance - radii[len(coords_list)] - radii[i]
                
                if edge_distance < min_distance_between_nodes:
                    valid = False
                    break
            
            if valid:
                coords_list.append(candidate)
            
            attempts += 1

        if len(coords_list) < num_nodes:
            raise ValueError(
                f"Failed to place all {num_nodes} nodes after {max_attempts} attempts. "
                f"Only placed {len(coords_list)} nodes. Try reducing num_nodes, "
                f"increasing map size, or decreasing min_distance_between_nodes."
            )

        # --- Step 3: Create Nodes ---
        nodes = [GameNode(coords, node_sizes[i]) for i, coords in enumerate(coords_list)]
        for node in nodes:
            world.add_node(node)

        # --- Step 4: Connect Nodes Without Path Intersection ---
        # Connect each node to its N nearest neighbors (at least one)
        # while preventing paths from crossing each other
        neighbor_count = min(3, num_nodes - 1)
        for node in nodes:
            distances = sorted(
                [(GameNode.distance(node, other), other) for other in nodes if other is not node],
                key=lambda x: x[0],
            )
            
            # Try to connect to nearest neighbors, skipping if path would intersect
            connections_made = 0
            for _, neighbor in distances:
                if connections_made >= neighbor_count:
                    break
                
                # Check if path already exists (in either direction)
                path_key_forward = (node, neighbor)
                path_key_backward = (neighbor, node)
                if path_key_forward in world._paths or path_key_backward in world._paths:
                    connections_made += 1
                    continue
                
                # Check if this new path would intersect with any existing path
                new_path_start = node.coords
                new_path_end = neighbor.coords
                intersects = False
                
                for (existing_node1, existing_node2) in world._paths.keys():
                    existing_path_start = existing_node1.coords
                    existing_path_end = existing_node2.coords
                    
                    if cls._segments_intersect(
                        new_path_start, 
                        new_path_end, 
                        existing_path_start, 
                        existing_path_end
                    ):
                        intersects = True
                        break
                
                # Only add path if it doesn't intersect
                if not intersects:
                    path = Path(node, neighbor)
                    world.add_path(path)
                    connections_made += 1

        return world


class Path(GameObject):
    """
    Represents a connection between two GameNodes.
    
    Armies move along paths with their position tracked as a float from 0 to distance.
    When position goes below 0 or above distance, the army moves to the connected node.
    """
    
    def __init__(self, game_node1: GameNode, game_node2: GameNode):
        """
        Create a path connecting two game nodes.
        
        Args:
            game_node1: First node (starting node)
            game_node2: Second node (ending node)
        """
        super().__init__()
        self._game_node1: GameNode = game_node1
        self._game_node2: GameNode = game_node2
        self._distance = GameNode.distance(self._game_node1, self._game_node2)
        
        # Armies on this path and their position (0 to distance)
        self._armies_and_coords: dict[Army, float] = {}

    @property
    def distance(self) -> float | int:
        """The length of this path between the two nodes."""
        return self._distance
    
    @property
    def min_position(self) -> float:
        """Minimum position on the path (at starting node)."""
        return 0.0
    
    @property
    def max_position(self) -> float:
        """Maximum position on the path (at ending node)."""
        return self.distance - 1
    
    def move_army(self, army: Army, delta: float) -> None:
        """
        Move an army along this path by a given distance.
        
        If the army's position goes below min_position or above max_position,
        the army is automatically moved to the connected node.
        
        Args:
            army: The army to move
            delta: The distance to move (can be negative)
        """
        if army in self._armies_and_coords.keys():
            self._armies_and_coords[army] += delta

            # If army goes below minimum position, move to first node
            if self._armies_and_coords[army] < self.min_position:
                army.get_on_gamenode(self._game_node1)

            # If army goes above maximum position, move to second node
            elif self._armies_and_coords[army] > self.max_position:
                army.get_on_gamenode(self._game_node2)

    def add_army(self, army: Army, from_node: GameNode) -> None:
        """
        Add an army to this path from one of its connected nodes.
        
        Args:
            army: The army to add to the path
            from_node: The node the army is coming from (must be one of the path's nodes)
            
        Raises:
            BadGameNodeException: If from_node is not one of this path's nodes
        """
        if not (from_node is self._game_node1 or from_node is self._game_node2):
            raise BadGameNodeException(
                f"Army must originate from one of the path's connected nodes. "
                f"Got node at ({from_node.x}, {from_node.y}) but path connects "
                f"({self._game_node1.x}, {self._game_node1.y}) to "
                f"({self._game_node2.x}, {self._game_node2.y})"
            )
        
        # Place army at the starting position on the path
        if from_node is self._game_node1:
            self._armies_and_coords.update({army: self.min_position})
        elif from_node is self._game_node2:
            self._armies_and_coords.update({army: self.max_position})

    def remove_army(self, army: Army) -> None:
        """
        Remove an army from this path.
        
        Args:
            army: The army to remove
        """
        del self._armies_and_coords[army]


class GameNode(GameObject):
    """
    Represents a location on the game map where mobile units can be stationed.
    
    Each node has:
    - Coordinates (x, y)
    - A size (perhaps for future expansion purposes)
    - A list of mobile unit groups currently stationed there
    - Optional City contained within (None if node is unclaimed)
    - Optional allegiance to an empire (None = unclaimed)
    
    Nodes can become claimed when 10+ Settlers are stationed and a City is established.
    A City can only exist on a node if it's claimed by an empire.
    """
    
    def __init__(self, coords: tuple[int, int], size: int):
        """
        Create a new game node at the given coordinates.
        
        Args:
            coords: (x, y) coordinates of this node
            size: The size/capacity of this node
        """
        super().__init__()
        self._x: int = coords[0]
        self._y: int = coords[1]
        self._size: int = size
        self._armies: list[Army] = []
        self._claimed_by_empire: Optional[Empire] = None
        self._city: Optional[City] = None  # City contained in this node

    def add_army(self, army: Army) -> None:
        """
        Station an army at this node.
        
        Args:
            army: The army to station here
        """
        self._armies.append(army)
    
    def armies(self) -> list[Army]:
        """Get all armies currently stationed at this node."""
        return self._armies

    def remove_army(self, army: Army) -> None:
        """
        Remove an army from this node.
        
        Args:
            army: The army to remove
        """
        self._armies.remove(army)

    @property
    def x(self) -> int:
        """X coordinate of this node."""
        return self._x
    
    @property
    def y(self) -> int:
        """Y coordinate of this node."""
        return self._y
    
    @property
    def coords(self) -> tuple[int, int]:
        """Coordinates of this node as (x, y) tuple."""
        return (self._x, self._y)
    
    @property
    def size(self) -> int:
        """Size/capacity of this node."""
        return self._size
    
    @property
    def is_claimed(self) -> bool:
        """Return True if this node has been claimed by an empire."""
        return self._claimed_by_empire is not None
    
    @property
    def claimed_by_empire(self) -> Optional[Empire]:
        """Get the empire that claimed this node, or None if unclaimed."""
        return self._claimed_by_empire
    
    def claim_for_empire(self, empire: Empire) -> None:
        """
        Mark this node as claimed by the given empire.
        
        Args:
            empire: The empire claiming this node
        """
        self._claimed_by_empire = empire
    
    @property
    def has_city(self) -> bool:
        """Return True if this node contains a city."""
        return self._city is not None
    
    @property
    def city(self) -> Optional[City]:
        """Get the city contained in this node, or None if unclaimed."""
        return self._city
    
    def set_city(self, city: City) -> None:
        """
        Set the city contained in this node.
        
        The city's size must not exceed the node's size.
        
        Args:
            city: The city to add to this node
            
        Raises:
            ValueError: If city size exceeds node size
        """
        if city.size > self._size:
            raise ValueError(
                f"City size ({city.size}) cannot exceed node size ({self._size})"
            )
        self._city = city
    
    def count_settler_units(self) -> int:
        """
        Count the number of Settler units currently stationed on this node.
        
        Settlers are passive units used for establishing new cities.
        
        Returns:
            Number of Settler units present
        """
        from ..unit_classes.passive_units import Settler
        settler_count = 0
        for group in self._armies:
            for unit in group.mobile_units:
                if isinstance(unit, Settler):
                    settler_count += 1
        return settler_count
    @property
    def size(self) -> int:
        return self._size
    @staticmethod
    def distance(game_node1: GameNode, game_node2: GameNode) -> float:
        """
        Calculate the Euclidean distance between two game nodes.
        
        Args:
            game_node1: First node
            game_node2: Second node
            
        Returns:
            The distance between the two nodes
        """
        x1 = game_node1.x
        y1 = game_node1.y
        x2 = game_node2.x
        y2 = game_node2.y
        return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)