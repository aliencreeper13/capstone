"""
FastAPI Backend Server for Civilization Empire Builder Game
Provides REST API for browser-based gameplay.

Behavior: Mimics playing from interactive_demo in terminal.
Backend runs native game logic with in-memory state (no database).
"""
# FIXME: HOLY CRAP THIS FILE IS OVER 2000 LINES
import asyncio
import threading
import time
import logging
import inspect
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import native game modules
import sys


desired_ideology_str = sys.argv[1]


# sys.path.insert(0, r'c:\Users\MrCheese\Desktop\Programming\Python\capstone') # TODO: Make it so that this temp fix isn't necessary
from .systems.government_actions import SubsidyAction
from .unit_classes import buildings
from .entities.city import City
from .entities.empire import Empire
from .entities.ideology import Anarchy, Communism, Monarchy, NeutralIdeology, Dictatorship, Republic, Socialism, Theocracy
from .gameplay.location import GameNode, WorldMap
from .gameplay.game import Game
from .systems.data import ExpendableCityResources
from .systems.job_requirements import JobRequirements
from .systems.job import CreationJob, DestructionJob, UpgradeJob


from .entities.building import Building

if desired_ideology_str.lower() == 'monarchy':
    desired_ideology = Monarchy()
elif desired_ideology_str.lower() == 'neutral':
    desired_ideology = NeutralIdeology()
elif desired_ideology_str == 'dictatorship':
    desired_ideology = Dictatorship()
elif desired_ideology_str.lower() == 'republic':
    desired_ideology = Republic()
elif desired_ideology_str.lower() == 'theocracy':
    desired_ideology = Theocracy()
elif desired_ideology_str.lower() == 'anarchy':
    desired_ideology = Anarchy()
elif desired_ideology_str.lower() == 'communism':
    desired_ideology = Communism()
elif desired_ideology_str.lower() == 'socialism':
    desired_ideology = Socialism()
else:
    print("Invalid ideology argument.")
    exit()
# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# API RESPONSE MODELS (for JSON serialization to frontend)
# ============================================================================

class ResourceData(BaseModel):
    food: float
    timber: float
    metal: float
    wealth: float

class PopulationData(BaseModel):
    total: int
    employable: int
    employed: int

class BuildingEffectData(BaseModel):
    """Data representing building contributions and effects"""
    food_per_tick: float = 0.0
    timber_per_tick: float = 0.0
    metal_per_tick: float = 0.0
    wealth_per_tick: float = 0.0
    knowledge_per_tick: float = 0.0
    morale_per_tick: float = 0.0
    food_storage: float = 0
    timber_storage: float = 0
    metal_storage: float = 0
    wealth_storage: float = 0
    population_capacity: float = 0
    defense: float = 0
    protection: float = 0
    new_workers_per_tick: float = 0.0
    new_population_per_tick: float = 0.0
    hp_regeneration_per_tick: float = 0
    max_lifespan_increase: int = 0

class BuildingData(BaseModel):
    id: str
    name: str
    level: int = 1
    space_used: int
    current_effect: BuildingEffectData = BuildingEffectData()
    next_level_effect: BuildingEffectData = BuildingEffectData()  # Shows 4% bonus preview
    upgrade_cost: dict = {"food": 0, "timber": 0, "metal": 0, "wealth": 0}

class UnitCompositionData(BaseModel):
    """Details of a single unit in an army."""
    type: str
    count: int
    name: str

class ArmyData(BaseModel):
    """Data for a single mobile unit group (army)."""
    id: str
    name: Optional[str] = None
    units: List[UnitCompositionData]
    unit_count: int
    total_size: int
    position: str
    location_name: str
    location: str
    allegiance: Optional[str]
    morale: Optional[float]
    current_hp: float
    max_hp: float
    damage_per_tick: float
    speed: float = 0
    is_halted: bool = False
    is_on_path: bool = False
    path_position: Optional[float] = None
    path_node1_coords: Optional[tuple[int, int]] = None
    path_node2_coords: Optional[tuple[int, int]] = None

class CityStateData(BaseModel):
    coords: tuple[int, int]
    name: str
    population: PopulationData
    resources: ResourceData
    resource_capacities: ResourceData
    morale: float
    defense: float = 100
    protection: float = 0
    hitpoints: float = 100
    max_hitpoints: float = 100
    buildings: List[BuildingData]
    armies: List[ArmyData] = []
    space_used: int
    space_total: int
    max_space: int

class EmpireStateData(BaseModel):
    name: str
    knowledge: float
    ideology: str
    capital_name: str
    total_population: PopulationData
    total_resources: ResourceData
    efficiency: float
    score: float
    num_cities: int

class GameStateResponse(BaseModel):
    current_tick: int
    empire: EmpireStateData
    selected_city: CityStateData
    last_update: str

class JobData(BaseModel):
    id: str
    building_type: str
    ticks_remaining: int
    ticks_total: int
    progress_percent: float
    is_upgrade: bool

class EventData(BaseModel):
    type: str
    unix_timestamp: int
    source: str
    description: str
    data: dict = {}
    triggered_by_ai: bool = False

class BuildingCreateRequest(BaseModel):
    building_type: str

class BuildingAction(BaseModel):
    building_id: str
    action: str

class CityExpandRequest(BaseModel):
    size_increase: int = 1

class ResourceTransferRequest(BaseModel):
    target_city_id: int
    food: float = 0
    timber: float = 0
    metal: float = 0
    wealth: float = 0

class BuildingRequirementData(BaseModel):
    building_name: str
    minimum_level: int
    current_level: int
    is_present: bool

class MobileUnitData(BaseModel):
    """Data for a mobile unit that can be created (troop or passive unit)."""
    unit_type: str
    name: str
    description: str
    size: int
    job_ticks: int
    is_troop: bool  # True for troops, False for passive units
    creation_cost: ResourceData
    building_requirements: List[BuildingRequirementData]
    can_create: bool  # True if all requirements are met

class AvailableMobileUnitsData(BaseModel):
    """Available mobile units for creation in a city."""
    troops: List[MobileUnitData]
    passive_units: List[MobileUnitData]

class MobileUnitCreateRequest(BaseModel):
    unit_type: str  # e.g., "Archer", "Settler"

# ============================================================================
# PHASE 4: ARMY MOVEMENT MODELS
# ============================================================================

class GameNodeData(BaseModel):
    """Data for a game node on the map."""
    id: str
    coords: tuple[int, int]
    size: int
    is_claimed: bool
    claimed_by: Optional[str]
    has_city: bool
    city_name: Optional[str]
    armies: List[str]  # IDs of armies at this node

class PathData(BaseModel):
    """Data for a path connecting two nodes."""
    id: str
    node1_id: str
    node2_id: str
    node1_coords: tuple[int, int]
    node2_coords: tuple[int, int]
    distance: float
    armies: List[dict]  # [{"army_id": str, "position": float, "eta": float}]

class MapStructureData(BaseModel):
    """Complete map structure: nodes and paths."""
    nodes: List[GameNodeData]
    paths: List[PathData]

class ArmyMovementRequest(BaseModel):
    """Request to move an army from its current location to adjacent node."""
    army_id: str
    destination_node_id: str

class ArmyStatusData(BaseModel):
    """Status of a moving army."""
    army_id: str
    status: str  # "stationary" or "moving"
    current_location: str  # node or path description
    destination: Optional[str]
    eta_ticks: Optional[int]
    units: List[UnitCompositionData]

# ============================================================================
# GAME SERVER (Native Game Logic)
# ============================================================================

class GameServer:
    """
    Manages game instance using native capstone classes.
    Runs like interactive_demo but serves via HTTP/WebSocket.
    """
    
    def __init__(self):
        # Native game objects (NOT database classes)
        self.game: Optional[Game] = None
        self.user_empire: Optional[Empire] = None
        self.capital_city: Optional[City] = None
        self.worldmap: Optional[WorldMap] = None
        #self.all_user_cities: List[City] = []  # Track all cities
        self.selected_city_idx: int = 0   # Index of currently selected city
        
        # Server state
        self.is_running = False
        self.tick_count = 0
        self.lock = threading.Lock()
        self.websocket_connections: List[WebSocket] = []
        
        # Building type mapping
        self.building_classes = {
            cls.name: cls
            for _, cls in inspect.getmembers(object=buildings, predicate=inspect.isclass)
            if hasattr(cls, "name")
        }

    def initialize(self):
        """Create new game using native classes (like starting new game in interactive_demo)."""
        logger.info("[*] Initializing game server (NATIVE GAME MODE)...")
        
        try:
            # --- Step 1: Generate random world map with nodes and paths ---
            # This creates a 200x200 map with 8 randomly placed nodes, connected by non-intersecting paths
            self.worldmap = WorldMap.generate_random_map(
                size=(200, 200),
                num_nodes=16,
                min_distance_between_nodes=30,
                node_sizes=15  # All nodes have size 15
            )
            nodes = self.worldmap.get_nodes()
            paths = self.worldmap.get_paths()
            logger.info(f"    ✓ World map generated (200x200) with {len(nodes)} nodes and {len(paths)} paths")
            logger.info(f"    ✓ Map seed: {self.worldmap.seed}")
            
            # Create game instance
            self.game = Game(self.worldmap)
            logger.info(f"    ✓ Game initialized")
            
            # Create ideology
            ideology = desired_ideology
            logger.info(f"    ✓ Neutral ideology created")
            
            # --- Step 2: Assign cities to generated nodes ---
            # Define city configurations with names and resources
            # We'll assign them to the first few nodes of the generated map
            city_configs = [
                {"name": "Capitol", "size": 10, "pop": 90, "wealth": 100, "food": 100, "timber": 50, "metal": 50},
                {"name": "Harbor Town", "size": 10, "pop": 50, "wealth": 80, "food": 120, "timber": 30, "metal": 20},
                {"name": "Mountain Fort", "size": 10, "pop": 25, "wealth": 60, "food": 80, "timber": 20, "metal": 80},
                {"name": "Forest Village", "size": 10, "pop": 15, "wealth": 50, "food": 150, "timber": 100, "metal": 10},
            ]
            
            # Ensure we don't try to create more cities than available nodes
            if len(city_configs) > len(nodes):
                logger.warning(f"    ⚠️  Only {len(nodes)} nodes available, limiting cities to {len(nodes)}")
                city_configs = city_configs[:len(nodes)]
            
            # Create cities and assign to nodes
            for i, config in enumerate(city_configs):
                node = nodes[i]
                city = City(gamenode=node, size=config["size"], morale=50.0)
                city.name = config["name"]
                city._resources.wealth = config["wealth"]
                city._resources.food = config["food"]
                city._resources.timber = config["timber"]
                city._resources.metal = config["metal"]
                # Add initial population (simplified aggregate system)
                city._societal_resources.population.add_population(config["pop"])
                city._societal_resources.population.add_employable(int(config["pop"] * 0.35))
                
                if i == 0:
                    # First city is the capital
                    self.capital_city = city
                    self.user_empire = Empire(autonomy=50, capital_city=self.capital_city, ideology=ideology)
                    self.user_empire.name = "New Empire"
                    self.user_empire.add_city(city)
                    self.game.add_empire(self.user_empire)
                    logger.info(f"    ✓ Capital city created: {config['name']} at {node.coords}")
                else:
                    # Additional cities
                    self.user_empire.add_city(city)
                    logger.info(f"    ✓ City created: {config['name']} at {node.coords}")
                
                # self.all_user_cities.append(city)
            #
            logger.info(f"    ✓ Creating enemy empire...")
            enemy_ideology = Monarchy()
            enemy_capital = None
            enemy_cities = []
            
            for i, config in enumerate(city_configs):
                node = nodes[4 + i]
                enemy_city = City(gamenode=node, size=config["size"], morale=50.0)
                enemy_city.name = f"Evil {config['name']}"
                enemy_city._resources.wealth = config["wealth"]
                enemy_city._resources.food = config["food"]
                enemy_city._resources.timber = config["timber"]
                enemy_city._resources.metal = config["metal"]
                enemy_city._societal_resources.population.add_population(config["pop"])
                enemy_city._societal_resources.population.add_employable(int(config["pop"] * 0.35))
                
                if i == 0:
                    enemy_capital = enemy_city
                
                enemy_cities.append(enemy_city)
                # self.all_user_cities.append(enemy_city)
            
            enemy_empire = Empire(autonomy=50, capital_city=enemy_capital, ideology=enemy_ideology)
            enemy_empire.name = "Enemy Empire"
            for enemy_city in enemy_cities:
                enemy_empire.add_city(enemy_city)
            self.game.add_empire(enemy_empire)
            logger.info(f"    ✓ Enemy empire created with {len(enemy_cities)} cities")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize game: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        logger.info(f"[✓] Game server initialized successfully (NATIVE MODE) - {len(self.all_user_cities)} cities on {len(nodes)} nodes\n")
    
    @property
    def all_user_cities(self) -> list[City]:
        """Get all cities belonging to the user's empire."""
        if self.user_empire is None:
            return []
        # return self.user_empire.cities
        return list(set(self.user_empire.cities)) # temp fix: Workaround duplicate references to capital city in empire

    def start_auto_tick(self):
        """Start auto-ticking in background thread."""
        self.is_running = True
        self.tick_thread = threading.Thread(target=self._tick_loop, daemon=True)
        self.tick_thread.start()
        logger.info("[*] Auto-tick thread started")
        
    def stop_auto_tick(self):
        """Stop auto-ticking."""
        self.is_running = False
        
    def _tick_loop(self):
        """Main game loop - calls next_tick() on native Game object."""
        tick_interval = 1.0  # 1 second per tick
        
        while self.is_running:
            try:
                with self.lock:
                    # Call native game's next_tick method
                    self.game.next_tick()
                    self.tick_count += 1
                    
                    if self.tick_count % 10 == 0:
                        # Log resource state for selected city
                        city = self.all_user_cities[self.selected_city_idx] if self.all_user_cities else self.capital_city
                        logger.info(f"[TICK {self.tick_count}] {city.name} Resources: "
                              f"F={city._resources.food:.0f}, "
                              f"T={city._resources.timber:.0f}, "
                              f"M={city._resources.metal:.0f}, "
                              f"W={city._resources.wealth:.0f}")
                        
                        # Log buildings
                        building_names = [b.__class__.__name__ for b in city._buildings]
                        
                        troop_names = []
                        for army in city._gamenode._armies:
                            for mobile_unit in army._mobile_units:
                                troop_names.append(mobile_unit.name)
                        # troop_names = [u.__class__.name for u in city._gamenode._armies]
                        logger.info(f"             Buildings: {building_names}")
                        logger.info(f"             Troops: {troop_names}")
                        logger.info(f"             Population: {city.total_population} ")
                        # logger.info(f"             Game Events: {city.allegiance.game_events}")
                        # logger.info(f"             Effects: {city._effects_with_ticks_left}")
                        logger.info(f"             Available space: {city._available_space}")
                time.sleep(tick_interval)
            except Exception as e:
                logger.error(f"[ERROR] in tick loop: {e}")
                import traceback
                traceback.print_exc()
    
    def _extract_building_effect_data(self, building) -> BuildingEffectData:
        """Extract effect data from a building at its current level."""
        effect = building.effect if hasattr(building, 'effect') else None
        if not effect:
            return BuildingEffectData()
        
        return BuildingEffectData(
            food_per_tick=effect.expendable_city_resources_per_tick.food,
            timber_per_tick=effect.expendable_city_resources_per_tick.timber,
            metal_per_tick=effect.expendable_city_resources_per_tick.metal,
            wealth_per_tick=effect.expendable_city_resources_per_tick.wealth,
            knowledge_per_tick=effect.expendable_empire_resources_per_tick.knowledge,
            morale_per_tick=effect.raw_morale_per_tick,
            food_storage=effect.expendable_city_resource_capacities_offered.food,
            timber_storage=effect.expendable_city_resource_capacities_offered.timber,
            metal_storage=effect.expendable_city_resource_capacities_offered.metal,
            wealth_storage=effect.expendable_city_resource_capacities_offered.wealth,
            population_capacity=effect.population_capacity_offered,
            defense=effect.city_base_defense_offered,
            protection=effect.city_base_protection_offered,
            new_workers_per_tick=effect.theoretical_new_employable_per_tick,
            new_population_per_tick=effect.theoretical_new_people_per_tick,
            hp_regeneration_per_tick=effect.city_hitpoint_regeneration_per_tick,
            max_lifespan_increase=effect.max_lifespan_increase
        )
    
    def _calculate_upgrade_bonus(self, current_value: float) -> float:
        """Calculate 4% upgrade bonus."""
        return current_value * 0.04

    
    def get_selected_city(self) -> City:
        """Get the currently selected city."""
        if not self.all_user_cities or self.selected_city_idx >= len(self.all_user_cities):
            return self.capital_city
        return self.all_user_cities[self.selected_city_idx]
    
    def select_city(self, city_id: int) -> Dict:
        """Select a city by index."""
        with self.lock:
            if city_id < 0 or city_id >= len(self.all_user_cities):
                raise ValueError(f"Invalid city ID: {city_id}")
            self.selected_city_idx = city_id
            city = self.all_user_cities[city_id]
            logger.info(f"[CITY SELECT] Switched to {city.name}")
            return {"status": "success", "city_id": city_id, "city_name": city.name}
    
    def get_cities_list(self) -> List[Dict]:
        """Get list of all cities with their basic info."""
        with self.lock:
            cities_data = []
            for i, city in enumerate(self.all_user_cities):
                cities_data.append({
                    "id": i,
                    "name": city.name,
                    "coords": city.gamenode.coords,
                    "population": city.total_population,
                    "is_selected": i == self.selected_city_idx,
                    "resources": {
                        "food": round(city._resources.food, 1),
                        "timber": round(city._resources.timber, 1),
                        "metal": round(city._resources.metal, 1),
                        "wealth": round(city._resources.wealth, 1),
                    },
                    "buildings_count": len(city._buildings),
                })
            return cities_data
    
    def _serialize_game_state(self) -> GameStateResponse:
        """
        Convert native game state to API response model.
        This bridges the native game with the REST API.
        """
        with self.lock:
            if not self.all_user_cities or not self.user_empire:
                raise HTTPException(status_code=500, detail="Game not initialized")
            
            city = self.get_selected_city()
            
            # Extract population stats from native City object
            total_pop = city.total_population
            employable = city.employable_population
            employed = len([j for j in city._running_jobs if j is not None])
            
            # Extract buildings from native City object
            buildings = []
            for i, building in enumerate(city._buildings):
                # Get current level effect data
                current_effect = self._extract_building_effect_data(building)
                
                # Calculate next level effect (with 4% bonus)
                next_level_effect = BuildingEffectData(
                    food_per_tick=current_effect.food_per_tick * 1.04,
                    timber_per_tick=current_effect.timber_per_tick * 1.04,
                    metal_per_tick=current_effect.metal_per_tick * 1.04,
                    wealth_per_tick=current_effect.wealth_per_tick * 1.04,
                    knowledge_per_tick=current_effect.knowledge_per_tick * 1.04,
                    morale_per_tick=current_effect.morale_per_tick * 1.04,
                    food_storage=int(current_effect.food_storage * 1.04),
                    timber_storage=int(current_effect.timber_storage * 1.04),
                    metal_storage=int(current_effect.metal_storage * 1.04),
                    wealth_storage=int(current_effect.wealth_storage * 1.04),
                    population_capacity=int(current_effect.population_capacity * 1.04),
                    defense=int(current_effect.defense * 1.04),
                    protection=int(current_effect.protection * 1.04),
                    new_workers_per_tick=current_effect.new_workers_per_tick * 1.04,
                    new_population_per_tick=current_effect.new_population_per_tick * 1.04,
                    hp_regeneration_per_tick=int(current_effect.hp_regeneration_per_tick * 1.04),
                    max_lifespan_increase=int(current_effect.max_lifespan_increase * 1.04)
                )
                
                # Calculate upgrade costs for next level
                upgrade_target_level = building._level + 1
                upgrade_costs = {
                    "food": building.creation_job_requirements.food(upgrade_target_level),
                    "timber": building.creation_job_requirements.timber(upgrade_target_level),
                    "metal": building.creation_job_requirements.metal(upgrade_target_level),
                    "wealth": building.creation_job_requirements.wealth(upgrade_target_level)
                }
                
                building_data = BuildingData(
                    id=f"building_{i}",
                    name=building.__class__.__name__,
                    level=building._level,
                    space_used=building.size,
                    current_effect=current_effect,
                    next_level_effect=next_level_effect,
                    upgrade_cost=upgrade_costs
                )
                buildings.append(building_data)
            
            # Extract resource capacities from native City object
            capacities = city.expendable_resource_capacities
            
            # Serialize armies in this city
            armies_data = []
            for army in city.gamenode.armies():
                armies_data.append(self._serialize_army(army, city.gamenode))
            
            # Serialize city state
            city_state = CityStateData(
                coords=city.gamenode.coords,
                name=city.name if hasattr(city, 'name') else "Capital",
                population=PopulationData(
                    total=int(total_pop),
                    employable=int(employable),
                    employed=int(employed)
                ),
                resources=ResourceData(
                    food=city._resources.food,
                    timber=city._resources.timber,
                    metal=city._resources.metal,
                    wealth=city._resources.wealth
                ),
                resource_capacities=ResourceData(
                    food=capacities.food,
                    timber=capacities.timber,
                    metal=capacities.metal,
                    wealth=capacities.wealth
                ),
                morale=city.morale,
                buildings=buildings,
                armies=armies_data,
                space_used=sum(b.size for b in city._buildings),
                space_total=city.size,
                max_space=city._gamenode.size,
                defense=city.defense,
                protection=city.protection,
                
            )
            
            # Serialize empire state
            empire_state = EmpireStateData(
                name=self.user_empire.name if hasattr(self.user_empire, 'name') else "Empire",
                knowledge=self.user_empire.knowledge,
                ideology=self.user_empire._ideology.__class__.__name__,
                capital_name=city.name if hasattr(city, 'name') else "Capital",
                total_population=PopulationData(
                    total=total_pop,
                    employable=employable,
                    employed=employed
                ),
                total_resources=ResourceData(
                    food=city._resources.food,
                    timber=city._resources.timber,
                    metal=city._resources.metal,
                    wealth=city._resources.wealth
                ),
                efficiency=self.user_empire.efficiency,
                score=self.user_empire.score,
                num_cities=len(self.user_empire.cities)
            )
            
            return GameStateResponse(
                current_tick=self.tick_count,
                empire=empire_state,
                selected_city=city_state,
                last_update=datetime.now().isoformat()
            )
    
    def create_building(self, building_type: str) -> Dict:
        """Create building in selected city using native objects."""
        with self.lock:
            
            city = self.get_selected_city()
            if not city:
                raise HTTPException(status_code=500, detail="City not initialized")
            
            try:
                if building_type not in self.building_classes:
                    raise ValueError(f"Unknown building type: {building_type}")
                
                # Create native building creation job
                building_class = self.building_classes[building_type]
                building_job = CreationJob(building_class)

                # Use City's add_job which returns (requirements_met, message, failures)
                requirements_met, message, failures = city.add_job(building_job)

                if not requirements_met:
                    logger.info(f"[BUILD FAILED] {building_type} in {city.name}: {message} - Failures: {failures}")
                    return {
                        "status": "error",
                        "message": message,
                        "failures": failures
                    }

                logger.info(f"[BUILD] {building_type} queued in {city.name} - {message}")
                return {
                    "status": "success",
                    "message": message,
                    "building": building_type
                }
                
            except Exception as e:
                logger.error(f"Error creating building: {e}")
                raise HTTPException(status_code=400, detail=str(e))
    
    def demolish_building(self, building_id: str) -> Dict:
        """Remove building from selected city."""
        with self.lock:
            city = self.get_selected_city()
            if not city:
                raise HTTPException(status_code=500, detail="City not initialized")
            
            try:

                building_idx = int(building_id.split("_")[-1])
                if not (0 <= building_idx < len(city._buildings)):
                    raise ValueError("Building not found")
                # destruction_job = DestructionJob(city._buildings[building_idx])
                removed = city._buildings.pop(building_idx)
                logger.info(f"[DEMOLISH] {removed.__class__.__name__} demolished from {city.name}")
                return {"status": "success", "building": removed.__class__.__name__}
                
            except Exception as e:
                logger.error(f"Error demolishing building: {e}")
                raise HTTPException(status_code=400, detail=str(e))
    
    def upgrade_building(self, building_id: str) -> Dict:
        """Submit an upgrade job for a building in the selected city."""
        with self.lock:
            city = self.get_selected_city()
            if not city:
                raise HTTPException(status_code=500, detail="City not initialized")
            
            try:
                building_idx = int(building_id.split("_")[-1])
                if not (0 <= building_idx < len(city._buildings)):
                    raise ValueError("Building not found")
                
                building = city._buildings[building_idx]
                old_level = building._level
                
                # Create an UpgradeJob instead of upgrading immediately
                # This queues the upgrade as a job that takes time to complete
                upgrade_job = UpgradeJob(building)
                
                requirements_met, message, failures = city.add_job(upgrade_job)
                if not requirements_met:
                    logger.info(f"[UPGRADE FAILED] {message} - Failures: {failures}")
                    return {
                        "status": "error",
                        "message": message,
                        "building": building.__class__.name,
                        "current_level": old_level,
                        "target_level": old_level + 1,
                        "failures": failures
                    }
                
                logger.info(f"[UPGRADE] Upgrade job submitted for {building.__class__.__name__} (Level {old_level} → {old_level + 1}) in {city.name}")
                return {
                    "status": "success",
                    "message": f"Upgrade job submitted for {building.__class__.__name__}",
                    "building": building.__class__.name,
                    "current_level": old_level,
                    "target_level": old_level + 1,
                    "failures": []
                }
                
            except Exception as e:
                logger.error(f"Error submitting upgrade job: {e}")
                raise HTTPException(status_code=400, detail=str(e))
    
    def expand_city(self, size_increase: int = 1) -> Dict:
        """Expand the selected city's size."""
        with self.lock:
            city = self.get_selected_city()
            if not city:
                raise HTTPException(status_code=500, detail="City not initialized")
            
            try:
                success, reason = city.expand_city(size_increase)
                
                if success:
                    logger.info(f"[EXPAND] {city.name} expanded by {size_increase} size unit(s)")
                    return {
                        "status": "success",
                        "message": reason,
                        "new_size": city.size,
                        "max_size": city._gamenode.size
                    }
                else:
                    logger.info(f"[EXPAND FAILED] {city.name}: {reason}")
                    return {
                        "status": "error",
                        "message": reason,
                        "current_size": city.size,
                        "max_size": city._gamenode.size
                    }
                    
            except Exception as e:
                logger.error(f"Error expanding city: {e}")
                raise HTTPException(status_code=400, detail=str(e))
    
    def transfer_resources(self, target_city_id: int, food: float, timber: float, metal: float, wealth: float) -> Dict:
        """Transfer resources from the selected city to a target city."""
        with self.lock:
            source_city = self.get_selected_city()
            if not source_city:
                raise HTTPException(status_code=500, detail="City not initialized")
            
            if target_city_id < 0 or target_city_id >= len(self.all_user_cities):
                raise HTTPException(status_code=400, detail=f"Invalid target city ID: {target_city_id}")
            
            target_city = self.all_user_cities[target_city_id]
            
            if source_city == target_city:
                raise HTTPException(status_code=400, detail="Cannot transfer resources to the same city")
            
            try:
                resources = ExpendableCityResources(
                    food=food,
                    timber=timber,
                    metal=metal,
                    wealth=wealth
                )
                
                success, message = source_city.transfer_resources_to_city(target_city, resources)
                
                if success:
                    logger.info(f"[TRANSFER] {source_city.name} initiated transfer to {target_city.name}: {resources}")
                    return {
                        "status": "success",
                        "message": message,
                        "source_city": source_city.name,
                        "target_city": target_city.name
                    }
                else:
                    logger.info(f"[TRANSFER FAILED] {source_city.name} -> {target_city.name}: {message}")
                    return {
                        "status": "error",
                        "message": message,
                        "source_city": source_city.name,
                        "target_city": target_city.name
                    }
                    
            except Exception as e:
                logger.error(f"Error transferring resources: {e}")
                raise HTTPException(status_code=400, detail=str(e))
    
    # TODO: This method should be simplified by utilizing preexisting logic in Empire.execute_government_action
    def execute_government_action(self, action_id: str) -> Dict:
        """Execute a government action (costs wealth from capital)."""
        with self.lock:
            if not self.capital_city or not self.user_empire:
                raise HTTPException(status_code=500, detail="Capital city or empire not initialized")
            
            try:
                # Find the matching government action from the ideology
                ideology_actions = self.user_empire._ideology.government_actions
                
                matched_action = None
                for act in ideology_actions:
                    # Build the same id as in get_available_government_actions
                    cls_name = type(act).__name__
                    act_id = cls_name.lower()
                    if hasattr(act, "intensity"):
                        act_id += f"_{getattr(act, 'intensity')}"
                    if hasattr(act, "campaign_type"):
                        act_id += f"_{getattr(act, 'campaign_type')}"
                    
                    if act_id == action_id:
                        matched_action = act
                        break
                
                if not matched_action:
                    raise ValueError(f"Unknown government action: {action_id}")
                
                wealth_cost = matched_action.cost_wealth(game_server.user_empire.efficiency)
                
                # Check if capital has enough wealth
                if self.capital_city._resources.wealth < wealth_cost:
                    raise ValueError(f"Insufficient wealth! Need {wealth_cost}, but only have {self.capital_city._resources.wealth:.0f}")
                
                # Deduct wealth from capital
                self.capital_city._resources.wealth -= wealth_cost
                
                # Apply the action's effect to the capital city
                effect = matched_action.get_effect()
                if effect.is_universal() or effect.capital_effect:
                    self.user_empire.add_universal_or_capital_effect(effect)
                else:
                    if isinstance(matched_action, SubsidyAction):
                        pass
                    self.capital_city.add_effect(effect)
                # self.capital_city._effects.append(effect)
                
                logger.info(f"[GOVERNMENT ACTION] {action_id} executed - Wealth cost: {wealth_cost} - Effect: {matched_action.description}")
                
                return {
                    "status": "success",
                    "action": action_id,
                    "wealth_cost": wealth_cost,
                    "effect": matched_action.description
                }
                
            except Exception as e:
                logger.error(f"Error executing government action: {e}")
                raise HTTPException(status_code=400, detail=str(e))
    
    def get_city_jobs(self, city_idx: Optional[int] = None) -> List[JobData]:
        """Get active jobs for a city."""
        with self.lock:
            city = self.all_user_cities[city_idx] if city_idx is not None else self.get_selected_city()
            if not city:
                raise HTTPException(status_code=500, detail="City not initialized")
            
            jobs = []
            for i, job in enumerate(city._running_jobs):
                if job is None:
                    continue
                    
                # Calculate progress
                ticks_total = job._original_ticks if hasattr(job, '_original_ticks') else 1
                ticks_remaining = max(0, job._num_ticks)
                progress_percent = ((ticks_total - ticks_remaining) / ticks_total) * 100 if ticks_total > 0 else 100
                
                # Get building type from result
                if job._is_upgrade:
                    building_type = job._result.__class__.__name__
                else:
                    building_type = job._result.__name__
                
                job_data = JobData(
                    id=f"job_{i}",
                    building_type=building_type,
                    ticks_remaining=int(ticks_remaining),
                    ticks_total=int(ticks_total),
                    progress_percent=round(progress_percent, 1),
                    is_upgrade=job._is_upgrade
                )
                jobs.append(job_data)
            
            return jobs
    
    def get_recent_events(self, limit: int = 50) -> List[EventData]:
        """Get recent game events from the empire."""
        with self.lock:
            if not self.user_empire:
                raise HTTPException(status_code=500, detail="Empire not initialized")
            
            # Get events from empire and convert to EventData
            events_list = self.user_empire.get_recent_events(count=limit)
            events = []
            for event in events_list:
                event_data = EventData(
                    type=event.type,
                    unix_timestamp=event.unix_timestamp,
                    source=event.source,
                    description=event.description,
                    data=event.data,
                    triggered_by_ai=event.triggered_by_ai
                )
                events.append(event_data)
            
            return events
    
    def get_available_mobile_units(self, city_idx: Optional[int] = None) -> AvailableMobileUnitsData:
        """Get available mobile units (troops and passive units) for creation in a city."""
        with self.lock:
            from .unit_classes.troops import Archer
            from .unit_classes.passive_units import Settler
            from .systems.job_requirements import ContingentOnInfo
            
            city = self.all_user_cities[city_idx] if city_idx is not None else self.get_selected_city()
            if not city:
                raise HTTPException(status_code=500, detail="City not initialized")
            
            # Get all available unit classes
            all_unit_classes = [Archer, Settler]
            
            troops = []
            passive_units = []
            
            for unit_class in all_unit_classes:
                # Check if unit is a troop (has damage_per_tick > 0)
                is_troop = hasattr(unit_class, 'base_attributes') and unit_class.base_attributes.damage_per_tick > 0
                
                # Get building requirements
                building_requirements = []
                can_create = True
                
                if hasattr(unit_class, 'job_requirements') and unit_class.job_requirements.unit_types_contingent_on:
                    for requirement in unit_class.job_requirements.unit_types_contingent_on:
                        # Find building in city
                        matching_buildings = [b for b in city._buildings if isinstance(b, requirement.unit_class)]
                        
                        if matching_buildings:
                            current_level = max(b._level for b in matching_buildings)
                            is_present = True
                        else:
                            current_level = 0
                            is_present = False
                        
                        if not is_present or current_level < requirement.minimum_level_needed:
                            can_create = False
                        
                        building_requirements.append(BuildingRequirementData(
                            building_name=requirement.unit_class.name,
                            minimum_level=requirement.minimum_level_needed,
                            current_level=current_level,
                            is_present=is_present
                        ))
                
                # Get creation cost
                job_reqs = unit_class.job_requirements
                creation_cost = job_reqs.expendable_city_resources_level1 if hasattr(job_reqs, 'expendable_city_resources_level1') else ExpendableCityResources()
                
                mobile_unit_data = MobileUnitData(
                    unit_type=unit_class.__name__,
                    name=unit_class.name,
                    description=unit_class.description,
                    size=unit_class.size,
                    job_ticks=unit_class.job_num_ticks,
                    is_troop=is_troop,
                    creation_cost=ResourceData(
                        food=creation_cost.food,
                        timber=creation_cost.timber,
                        metal=creation_cost.metal,
                        wealth=creation_cost.wealth
                    ),
                    building_requirements=building_requirements,
                    can_create=can_create
                )
                
                if is_troop:
                    troops.append(mobile_unit_data)
                else:
                    passive_units.append(mobile_unit_data)
            
            return AvailableMobileUnitsData(troops=troops, passive_units=passive_units)
    
    def create_mobile_unit(self, unit_type: str) -> Dict:
        """Create a mobile unit (troop or passive unit) in the selected city."""
        with self.lock:
            from .unit_classes.troops import Archer
            from .unit_classes.passive_units import Settler
            from .systems.job import CreationJob
            
            city = self.get_selected_city()
            if not city:
                raise HTTPException(status_code=500, detail="City not initialized")
            
            try:
                # Map unit type names to classes
                unit_classes = {
                    "Archer": Archer,
                    "Settler": Settler,
                }
                
                if unit_type not in unit_classes:
                    raise ValueError(f"Unknown mobile unit type: {unit_type}")
                
                unit_class = unit_classes[unit_type]
                
                # Create creation job for the mobile unit
                creation_job = CreationJob(unit_class)
                requirements_met, message, failures =  city.add_job(creation_job)
                
                logger.info(f"[CREATE] {unit_type} job created in {city.name}")
                return {"status": "success", "unit_type": unit_type}
                
            except Exception as e:
                logger.error(f"Error creating mobile unit: {e}")
                raise HTTPException(status_code=400, detail=str(e))
    
    # ========== PHASE 4: ARMY MOVEMENT METHODS ==========
    
    def _get_army_id(self, army) -> str:
        """Generate unique ID for an army."""
        # Use object id as unique identifier
        return f"army_{id(army)}"
    
    def _get_node_id(self, node) -> str:
        """Generate unique ID for a game node."""
        return f"node_{node.x}_{node.y}"
    
    def _get_path_id(self, path) -> str:
        """Generate unique ID for a path."""
        n1 = path._game_node1
        n2 = path._game_node2
        return f"path_{n1.x}_{n1.y}_to_{n2.x}_{n2.y}"
    
    def get_all_armies(self) -> List[ArmyData]:
        """Get all armies across all nodes and paths."""
        with self.lock:
            armies = []
            
            if not self.worldmap:
                return armies
            
            # Collect armies from all nodes
            for node in self.worldmap.get_nodes():
                for army in node.armies():
                    armies.append(self._serialize_army(army, node, None))
            
            # Collect armies on all paths
            for (node1, node2), path in self.worldmap.get_paths().items():
                for army, position in path._armies_and_coords.items():
                    armies.append(self._serialize_army_on_path(army, path, position))
            
            return armies
    
    def _serialize_army(self, army, gamenode=None, path=None) -> ArmyData:
        """Convert a MobileUnitGroup to ArmyData for API response."""
        # Get unit composition
        units_dict: Dict[str, int] = {}
        for unit in army._mobile_units:
            unit_type = unit.__class__.__name__
            units_dict[unit_type] = units_dict.get(unit_type, 0) + 1
        
        units = []
        for unit_type, count in units_dict.items():
            units.append(UnitCompositionData(
                type=unit_type,
                count=count,
                name=getattr(unit.__class__, 'name', unit_type)
            ))
        
        # Get position
        if gamenode:
            position = self._get_node_id(gamenode)
            location_name = gamenode.city.name if gamenode.has_city else f"Node ({gamenode.x}, {gamenode.y})"
            location = location_name
        else:
            position = f"unknown"
            location_name = "Unknown"
            location = "Unknown"
        
        # Get combat attributes
        current_attrs = army.current_attributes
        
        return ArmyData(
            id=self._get_army_id(army),
            name=f"Army {self._get_army_id(army)[:8]}",
            units=units,
            unit_count=len(army._mobile_units),
            total_size=len(army._mobile_units),
            position=position,
            location_name=location_name,
            location=location,
            allegiance=army._allegiance.name if army._allegiance else None,
            morale=current_attrs.morale if current_attrs else 50.0,
            current_hp=current_attrs.hitpoints if current_attrs else 0,
            max_hp=current_attrs.hitpoints if current_attrs else 0,
            damage_per_tick=current_attrs.damage_per_tick if current_attrs else 0,
            speed=current_attrs.speed if current_attrs else 0,
            is_halted=getattr(army, '_is_halted', False),
            is_on_path=False
        )
    
    def _serialize_army_on_path(self, army, path, position: float) -> ArmyData:
        """Convert a moving army to ArmyData."""
        units_dict: Dict[str, int] = {}
        for unit in army._mobile_units:
            unit_type = unit.__class__.__name__
            units_dict[unit_type] = units_dict.get(unit_type, 0) + 1
        
        units = []
        for unit_type, count in units_dict.items():
            units.append(UnitCompositionData(
                type=unit_type,
                count=count,
                name=getattr(unit.__class__, 'name', unit_type)
            ))
        
        n1_coords = path._game_node1.coords
        n2_coords = path._game_node2.coords
        position_str = f"path_{n1_coords[0]}_{n1_coords[1]}_to_{n2_coords[0]}_{n2_coords[1]}"
        
        # Get combat attributes
        current_attrs = army.current_attributes
        
        return ArmyData(
            id=self._get_army_id(army),
            name=f"Army {self._get_army_id(army)[:8]}",
            units=units,
            unit_count=len(army._mobile_units),
            total_size=len(army._mobile_units),
            position=f"{position_str}@{position:.1f}",
            location_name=f"En route ({position:.1f}/{path.distance:.1f})",
            location=f"Traveling",
            allegiance=army._allegiance.name if army._allegiance else None,
            morale=current_attrs.morale if current_attrs else 50.0,
            current_hp=current_attrs.hitpoints if current_attrs else 0,
            max_hp=current_attrs.hitpoints if current_attrs else 0,
            damage_per_tick=current_attrs.damage_per_tick if current_attrs else 0,
            speed=current_attrs.speed if current_attrs else 0,
            is_halted=getattr(army, '_is_halted', False),
            is_on_path=True,
            path_position=position,
            path_node1_coords=n1_coords,
            path_node2_coords=n2_coords
        )
    
    def get_map_structure(self) -> MapStructureData:
        """Get complete map structure (nodes and paths) for frontend."""
        with self.lock:
            if not self.worldmap:
                return MapStructureData(nodes=[], paths=[])
            
            nodes_data = []
            node_id_map = {}  # Map node object to its string ID
            
            # Serialize all nodes
            for node in self.worldmap.get_nodes():
                node_id = self._get_node_id(node)
                node_id_map[node] = node_id
                
                army_ids = [self._get_army_id(army) for army in node.armies()]
                
                nodes_data.append(GameNodeData(
                    id=node_id,
                    coords=node.coords,
                    size=node.size,
                    is_claimed=node.is_claimed,
                    claimed_by=node.claimed_by_empire.name if node.claimed_by_empire else None,
                    has_city=node.has_city,
                    city_name=node.city.name if node.has_city else None,
                    armies=army_ids
                ))
            
            # Serialize all paths
            paths_data = []
            for (node1, node2), path in self.worldmap.get_paths().items():
                armies_on_path = []
                for army, pos in path._armies_and_coords.items():
                    armies_on_path.append({
                        "army_id": self._get_army_id(army),
                        "position": pos,
                        "eta": None  # TODO: calculate ETA
                    })
                
                paths_data.append(PathData(
                    id=self._get_path_id(path),
                    node1_id=node_id_map.get(node1, self._get_node_id(node1)),
                    node2_id=node_id_map.get(node2, self._get_node_id(node2)),
                    node1_coords=node1.coords,
                    node2_coords=node2.coords,
                    distance=path.distance,
                    armies=armies_on_path
                ))
            
            return MapStructureData(nodes=nodes_data, paths=paths_data)
    
    def get_adjacent_nodes(self, node_id: str) -> List[GameNodeData]:
        """Get all nodes adjacent to a given node via paths."""
        with self.lock:
            if not self.worldmap:
                return []
            
            # Find the node by ID
            target_node = None
            for node in self.worldmap.get_nodes():
                if self._get_node_id(node) == node_id:
                    target_node = node
                    break
            
            if not target_node:
                return []
            
            adjacent = []
            paths = self.worldmap.get_paths()
            
            # Find all paths connected to this node
            for (node1, node2), path in paths.items():
                adjacent_node = None
                if node1 is target_node:
                    adjacent_node = node2
                elif node2 is target_node:
                    adjacent_node = node1
                
                if adjacent_node:
                    army_ids = [self._get_army_id(army) for army in adjacent_node.armies()]
                    adjacent.append(GameNodeData(
                        id=self._get_node_id(adjacent_node),
                        coords=adjacent_node.coords,
                        size=adjacent_node.size,
                        is_claimed=adjacent_node.is_claimed,
                        claimed_by=adjacent_node.claimed_by_empire.name if adjacent_node.claimed_by_empire else None,
                        has_city=adjacent_node.has_city,
                        city_name=adjacent_node.city.name if adjacent_node.has_city else None,
                        armies=army_ids
                    ))
            
            return adjacent
    
    def move_army(self, army_id: str, destination_node_id: str) -> Dict:
        """Move an army from its current location to an adjacent node."""
        with self.lock:
            if not self.worldmap:
                raise HTTPException(status_code=500, detail="World map not initialized")
            
            # Find the army
            source_army = None
            source_node = None
            
            for node in self.worldmap.get_nodes():
                for army in node.armies():
                    if self._get_army_id(army) == army_id:
                        source_army = army
                        source_node = node
                        break
                if source_army:
                    break
            
            if not source_army:
                raise HTTPException(status_code=404, detail=f"Army not found: {army_id}")
            
            if not source_node:
                raise HTTPException(status_code=400, detail="Army not at a node")
            
            # Find destination node
            dest_node = None
            for node in self.worldmap.get_nodes():
                if self._get_node_id(node) == destination_node_id:
                    dest_node = node
                    break
            
            if not dest_node:
                raise HTTPException(status_code=404, detail=f"Destination node not found: {destination_node_id}")
            
            # Find path between source and destination
            path = None
            paths = self.worldmap.get_paths()
            for (node1, node2), p in paths.items():
                if (node1 is source_node and node2 is dest_node) or (node2 is source_node and node1 is dest_node):
                    path = p
                    break
            
            if not path:
                raise HTTPException(status_code=400, detail=f"No path between nodes")
            
            # Move army onto the path
            try:
                source_army.get_on_path_and_start_moving(path)
                
                logger.info(f"[MOVEMENT] Army moved from {source_node.coords} to path toward {dest_node.coords}")
                return {
                    "status": "success",
                    "message": "Army started movement",
                    "army_id": army_id,
                    "destination": self._get_node_id(dest_node),
                    "distance": path.distance
                }
            except Exception as e:
                logger.error(f"Error moving army: {e}")
                raise HTTPException(status_code=400, detail=str(e))
    
    def halt_army(self, army_id: str) -> Dict:
        """Halt an army's movement on a path."""
        with self.lock:
            if not self.worldmap:
                raise HTTPException(status_code=500, detail="World map not initialized")
            
            # Find the army
            source_army = None
            for path_key, path in self.worldmap.get_paths().items():
                if army_id in [self._get_army_id(a) for a in path._armies_and_coords.keys()]:
                    for army in path._armies_and_coords.keys():
                        if self._get_army_id(army) == army_id:
                            source_army = army
                            break
                if source_army:
                    break
            
            if not source_army:
                raise HTTPException(status_code=404, detail=f"Army not found on path: {army_id}")
            
            if not source_army.on_path():
                raise HTTPException(status_code=400, detail="Army is not on a path")
            
            # Halt the army
            source_army._is_halted = True
            logger.info(f"[MOVEMENT] Army {army_id} halted")
            return {
                "status": "success",
                "message": "Army halted",
                "army_id": army_id
            }
    
    def resume_army(self, army_id: str) -> Dict:
        """Resume an army's movement on a path."""
        with self.lock:
            if not self.worldmap:
                raise HTTPException(status_code=500, detail="World map not initialized")
            
            # Find the army
            source_army = None
            for path_key, path in self.worldmap.get_paths().items():
                if army_id in [self._get_army_id(a) for a in path._armies_and_coords.keys()]:
                    for army in path._armies_and_coords.keys():
                        if self._get_army_id(army) == army_id:
                            source_army = army
                            break
                if source_army:
                    break
            
            if not source_army:
                raise HTTPException(status_code=404, detail=f"Army not found on path: {army_id}")
            
            if not source_army.on_path():
                raise HTTPException(status_code=400, detail="Army is not on a path")
            
            # Resume the army
            source_army._is_halted = False
            logger.info(f"[MOVEMENT] Army {army_id} resumed")
            return {
                "status": "success",
                "message": "Army resumed",
                "army_id": army_id
            }
    
    def reverse_army(self, army_id: str) -> Dict:
        """Reverse an army's direction on a path."""
        with self.lock:
            if not self.worldmap:
                raise HTTPException(status_code=500, detail="World map not initialized")
            
            # Find the army
            source_army = None
            source_path = None
            for path_key, path in self.worldmap.get_paths().items():
                if army_id in [self._get_army_id(a) for a in path._armies_and_coords.keys()]:
                    for army in path._armies_and_coords.keys():
                        if self._get_army_id(army) == army_id:
                            source_army = army
                            source_path = path
                            break
                if source_army:
                    break
            
            if not source_army:
                raise HTTPException(status_code=404, detail=f"Army not found on path: {army_id}")
            
            if not source_army.on_path():
                raise HTTPException(status_code=400, detail="Army is not on a path")
            
            # Reverse the army
            current_position = source_path._armies_and_coords[source_army]
            new_position = source_path.distance - current_position
            source_path._armies_and_coords[source_army] = new_position
            
            if not hasattr(source_army, '_direction_reversed'):
                source_army._direction_reversed = False
            source_army._direction_reversed = not source_army._direction_reversed
            
            logger.info(f"[MOVEMENT] Army {army_id} reversed at position {current_position}")
            return {
                "status": "success",
                "message": "Army direction reversed",
                "army_id": army_id,
                "new_position": new_position
            }

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Civilization Empire Builder (Native Mode)", 
    version="1.0.0-native"
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global game server
game_server = GameServer()

# ============================================================================
# STARTUP / SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize game on startup."""
    game_server.initialize()
    game_server.start_auto_tick()
    logger.info("[✓] Backend server started (NATIVE MODE)")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    game_server.stop_auto_tick()
    logger.info("[✓] Backend server stopped")

# ============================================================================
# REST API ENDPOINTS
# ============================================================================

@app.get("/api/game/state")
async def get_game_state():
    """Get current game state (native objects serialized to JSON)."""
    return game_server._serialize_game_state()

@app.post("/api/building/create")
async def create_building(request: BuildingCreateRequest):
    """Create a new building in capital city."""
    result = game_server.create_building(request.building_type)
    return {
        "status": "success", 
        "message": f"{request.building_type} created",
        "building": result["building"]
    }

@app.post("/api/building/action")
async def building_action(request: BuildingAction):
    """Perform action on a building (demolish or upgrade)."""
    if request.action == "demolish":
        result = game_server.demolish_building(request.building_id)
        return {
            "status": "success",
            "message": f"{result['building']} demolished"
        }
    elif request.action == "upgrade":
        result = game_server.upgrade_building(request.building_id)
        return result
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")

@app.post("/api/city/expand")
async def expand_city(request: CityExpandRequest):
    """Expand the selected city's size (building space)."""
    result = game_server.expand_city(request.size_increase)
    return result

@app.post("/api/city/transfer")
async def transfer_resources(request: ResourceTransferRequest):
    """Transfer resources from the selected city to a target city."""
    
    result = game_server.transfer_resources(
        target_city_id=request.target_city_id,
        food=request.food,
        timber=request.timber,
        metal=request.metal,
        wealth=request.wealth
    )
    return result

@app.get("/api/buildings/available")
async def get_available_buildings():
    """Get list of available building types with construction requirements for level 1."""
    building_classes = game_server.building_classes.values()
    
    buildings = []
    for building_class in building_classes:
        # Get level 1 requirements
        req = building_class.job_requirements
        resources = req.city_resources(level=1)
        workers = req.workers_needed(level=1)
        
        # Only include meaningful requirements (non-zero values)
        building_reqs = {}
        if resources.food > 0:
            building_reqs["food"] = resources.food
        if resources.timber > 0:
            building_reqs["timber"] = resources.timber
        if resources.metal > 0:
            building_reqs["metal"] = resources.metal
        if resources.wealth > 0:
            building_reqs["wealth"] = resources.wealth
        
        # Get category (default to UNCATEGORIZED if not defined)
        category = getattr(building_class, 'category', None)
        category_name = category.value if category else "Uncategorized"
        
        buildings.append({
            "name": building_class.name,
            "size": building_class.size,
            "description": building_class.description,
            "job_num_ticks": building_class.job_num_ticks,
            "category": category_name,
            "requirements": {
                "resources": building_reqs,
                "workers": workers,
                "knowledge": req.knowledge(level=1) if req.knowledge(level=1) > 0 else None
            }
        })
    
    return {
        "buildings": buildings
    }

# ============================================================================
# CITY MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/cities/list")
async def list_cities():
    """Get list of all cities with their status."""
    cities = game_server.get_cities_list()
    return {
        "status": "success",
        "cities": cities,
        "total": len(cities),
        "selected_city_id": game_server.selected_city_idx
    }

@app.post("/api/cities/select/{city_id}")
async def select_city(city_id: int):
    """Select a city to manage."""
    try:
        result = game_server.select_city(city_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# JOB QUEUE ENDPOINTS
# ============================================================================

@app.get("/api/city/jobs")
async def get_city_jobs():
    """Get active jobs for the selected city."""
    try:
        jobs = game_server.get_city_jobs()
        return {
            "status": "success",
            "jobs": jobs,
            "total": len(jobs)
        }
    except Exception as e:
        logger.error(f"Error getting city jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# GAME EVENTS ENDPOINTS
# ============================================================================

@app.get("/api/events")
async def get_game_events(limit: int = 50):
    """Get recent game events."""
    try:
        events = game_server.get_recent_events(limit=limit)
        return {
            "status": "success",
            "events": events,
            "total": len(events)
        }
    except Exception as e:
        logger.error(f"Error getting game events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# MOBILE UNITS ENDPOINTS
# ============================================================================

@app.get("/api/mobile-units/available")
async def get_available_mobile_units():
    """Get available mobile units (troops and passive units) for creation."""
    try:
        units = game_server.get_available_mobile_units()
        return {
            "status": "success",
            "troops": units.troops,
            "passive_units": units.passive_units
        }
    except Exception as e:
        logger.error(f"Error getting available mobile units: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mobile-units/create")
async def create_mobile_unit(request: MobileUnitCreateRequest):
    """Create a mobile unit (troop or passive unit)."""
    try:
        result = game_server.create_mobile_unit(request.unit_type)
        return result
    except Exception as e:
        logger.error(f"Error creating mobile unit: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# PHASE 4: ARMY MOVEMENT ENDPOINTS
# ============================================================================

@app.get("/api/armies")
async def get_all_armies():
    """Get all armies across the map (at nodes and on paths)."""
    try:
        armies = game_server.get_all_armies()
        return {
            "status": "success",
            "armies": armies,
            "total": len(armies)
        }
    except Exception as e:
        logger.error(f"Error getting armies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/map/structure")
async def get_map_structure():
    """Get complete map structure (nodes and paths) with army positions."""
    try:
        map_data = game_server.get_map_structure()
        return {
            "status": "success",
            "nodes": map_data.nodes,
            "paths": map_data.paths,
            "total_nodes": len(map_data.nodes),
            "total_paths": len(map_data.paths)
        }
    except Exception as e:
        logger.error(f"Error getting map structure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gamenode/{node_id}/adjacent")
async def get_adjacent_nodes(node_id: str):
    """Get all nodes adjacent to a given node via paths."""
    try:
        adjacent = game_server.get_adjacent_nodes(node_id)
        return {
            "status": "success",
            "node_id": node_id,
            "adjacent_nodes": adjacent,
            "total": len(adjacent)
        }
    except Exception as e:
        logger.error(f"Error getting adjacent nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/armies/{army_id}/move")
async def move_army(army_id: str, request: ArmyMovementRequest):
    """Move an army from its current location to an adjacent node."""
    try:
        result = game_server.move_army(army_id, request.destination_node_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error moving army: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/armies/{army_id}/halt")
async def halt_army(army_id: str):
    """Halt an army's movement on a path."""
    try:
        result = game_server.halt_army(army_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error halting army: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/armies/{army_id}/resume")
async def resume_army(army_id: str):
    """Resume an army's movement on a path."""
    try:
        result = game_server.resume_army(army_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming army: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/armies/{army_id}/reverse")
async def reverse_army(army_id: str):
    """Reverse an army's direction on a path."""
    try:
        result = game_server.reverse_army(army_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reversing army: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# GAME INFO ENDPOINTS
# ============================================================================

@app.post("/api/game/save")
async def save_game():
    """
    In-memory mode: Save endpoint returns success but doesn't persist.
    """
    return {
        "status": "success",
        "message": "Game state saved to memory (not persisted)",
        "tick": game_server.tick_count,
        "mode": "in-memory-native"
    }

@app.post("/api/game/load/{game_id}")
async def load_game(game_id: int):
    """
    In-memory mode: No load capability.
    """
    return {
        "status": "error",
        "message": "Load not supported in native in-memory mode. Restart server to reset.",
        "mode": "in-memory-native"
    }

@app.get("/api/game/info")
async def get_game_info():
    """Get current game information."""
    return {
        "mode": "native-in-memory",
        "tick": game_server.tick_count,
        "status": "running" if game_server.is_running else "stopped",
        "note": "Running native capstone game logic. No database persistence.",
        "version": "1.0.0-native",
        "empire_name": game_server.user_empire.name if game_server.user_empire else None,
        "capital_name": game_server.capital_city.name if game_server.capital_city else None,
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "mode": "native-in-memory",
        "game_initialized": game_server.game is not None,
        "tick": game_server.tick_count
    }

# ============================================================================
# MAP VISUALIZATION
# ============================================================================

@app.get("/api/map/worldmap-data")
async def get_worldmap_data():
    """
    Get world map data including seed, nodes, and paths.
    This allows the frontend to render the map client-side.
    """
    try:
        worldmap = game_server.worldmap
        
        # Get all cities (player's empire)
        player_empire = game_server.user_empire
        player_cities = {city.gamenode.coords: city for city in player_empire.cities} if player_empire else {}
        
        # Build node data
        nodes = []
        for node in worldmap.get_nodes():
            node_coords = tuple(node.coords)
            is_player_city = node_coords in player_cities
            
            nodes.append({
                "id": str(id(node)),  # Use Python object id as unique identifier
                "coords": list(node.coords),
                "is_claimed": is_player_city,
                "city_name": player_cities[node_coords].name if is_player_city else None,
                "is_friendly": is_player_city,  # For now, only player's cities are friendly
                "size": node.size
            })
        
        # Build path data (as simple connections between nodes)
        paths = []
        path_dict = worldmap.get_paths()
        for (node1, node2), path in path_dict.items():
            paths.append({
                "id": str(id(path)),
                "from_coords": list(node1.coords),
                "to_coords": list(node2.coords),
                "distance": path.distance
            })
        
        return {
            "seed": worldmap.seed,
            "size": worldmap._size,
            "nodes": nodes,
            "paths": paths
        }
    except Exception as e:
        logger.error(f"Error fetching worldmap data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/map/visualization")
async def get_map_visualization():
    """Get world map visualization as PNG image."""
    try:
        if not game_server.worldmap:
            raise HTTPException(status_code=500, detail="World map not initialized")
        
        # Visualize the map to a temporary file
        map_path = "worldmap_temp.png"
        game_server.worldmap.visualize(output_path=map_path, scale=1.0)
        
        # Read and return the file
        return FileResponse(map_path, media_type="image/png")
        
    except Exception as e:
        logger.error(f"Error generating map visualization: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate map: {str(e)}")

# ============================================================================
# GOVERNMENT ACTIONS
# ============================================================================

class GovernmentActionRequest(BaseModel):
    action_id: str
# ...existing code...
@app.get("/api/government/available-actions")
async def get_available_government_actions():
    """Get available government actions for the current empire/ideology."""
    try:
        with game_server.lock:
            if not game_server.user_empire or not game_server.user_empire._ideology:
                # Fallback to empty list if no empire/ideology initialized
                return {"actions": []}

            # Determine an efficiency value to present cost estimates with.
            efficiency = game_server.user_empire.efficiency

            ideology_actions = game_server.user_empire._ideology.government_actions

            actions = []
            for act in ideology_actions:
                cls_name = type(act).__name__
                act_id = cls_name.lower()
                if hasattr(act, "intensity"):
                    act_id += f"_{getattr(act, 'intensity')}"
                if hasattr(act, "campaign_type"):
                    act_id += f"_{getattr(act, 'campaign_type')}"
                # Normalize fields for frontend, call cost_wealth as function with efficiency
                try:
                    cost_val = act.cost_wealth(efficiency)
                except Exception:
                    # fallback if something unexpected
                    cost_val = getattr(act, "_cost_wealth", 0)
                    # print("something went wrongg")

                actions.append({
                    "id": act_id,
                    "name": getattr(act, "name", cls_name),
                    "description": getattr(act, "description", ""),
                    "icon": getattr(act, "icon", None) or "",
                    "cost_wealth": cost_val,
                    "duration_ticks": getattr(act, "duration_ticks", 0),
                    "effect": getattr(act, "description", ""),
                    "category": getattr(act, "category", "government")
                })

            return {"actions": actions}
    except Exception as e:
        logger.error(f"Error getting government actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# ...existing code...

@app.post("/api/government/action")
async def execute_government_action(request: GovernmentActionRequest):
    """Execute a government action (costs wealth from capital)."""
    try:
        result = game_server.execute_government_action(request.action_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing government action: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# WEBSOCKET
# ============================================================================

@app.websocket("/ws/game")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    game_server.websocket_connections.append(websocket)
    
    try:
        while True:
            # Broadcast current game state every second
            state = game_server._serialize_game_state()
            await websocket.send_json(state.dict())
            await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if websocket in game_server.websocket_connections:
            game_server.websocket_connections.remove(websocket)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CIVILIZATION EMPIRE BUILDER - BACKEND SERVER (NATIVE GAME MODE)")
    print("=" * 80)
    print("Mode: Running native capstone game logic")
    print("Persistence: In-memory only (game state lost on server restart)")
    print("Behavior: Like playing from interactive_demo terminal, but via HTTP/WebSocket")
    print("=" * 80 + "\n")
    # Disable HTTP access logs from uvicorn (keeps your app logger output)
    import logging
    logging.getLogger("uvicorn.access").disabled = True
    # Optionally raise uvicorn.error / fastapi logger levels to reduce noise:
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=False
    )