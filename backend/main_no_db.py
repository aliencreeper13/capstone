"""
FastAPI Backend Server for Civilization Empire Builder Game
Provides REST API for browser-based gameplay.

Behavior: Mimics playing from interactive_demo in terminal.
Backend runs native game logic with in-memory state (no database).
"""

import asyncio
import threading
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import native game modules
import sys


sys.path.insert(0, r'c:\Users\MrCheese\Desktop\Programming\Python\capstone')

from backend.entities.city import City
from backend.entities.empire import Empire
from backend.entities.ideology import NeutralIdeology
from backend.gameplay.location import GameNode, WorldMap
from backend.gameplay.game import Game
from backend.systems.data import ExpendableCityResources
from backend.systems.job_requirements import JobRequirements
from backend.systems.job import CreationJob, DestructionJob

# Import building classes from interactive_demo for creation
from interactive_demo import (
    Farm, Market, School, WoodcuttersCamp, Mine, 
    Library, Temple, Housing, Granary, LumberYard,
    University, Hospital
)

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

class BuildingData(BaseModel):
    id: str
    name: str
    level: int = 1
    space_used: int

class CityStateData(BaseModel):
    coords: tuple[int, int]
    name: str
    population: PopulationData
    resources: ResourceData
    resource_capacities: ResourceData
    morale: float
    defense: float = 100
    hitpoints: float = 100
    max_hitpoints: float = 100
    buildings: List[BuildingData]
    space_used: int
    space_total: int

class EmpireStateData(BaseModel):
    name: str
    knowledge: float
    ideology: str
    capital_name: str
    total_population: PopulationData
    total_resources: ResourceData

class GameStateResponse(BaseModel):
    current_tick: int
    empire: EmpireStateData
    selected_city: CityStateData
    last_update: str

class BuildingCreateRequest(BaseModel):
    building_type: str

class BuildingAction(BaseModel):
    building_id: str
    action: str

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
        self.empire: Optional[Empire] = None
        self.capital_city: Optional[City] = None
        self.worldmap: Optional[WorldMap] = None
        self.all_cities: List[City] = []  # Track all cities
        self.selected_city_idx: int = 0   # Index of currently selected city
        
        # Server state
        self.is_running = False
        self.tick_count = 0
        self.lock = threading.Lock()
        self.websocket_connections: List[WebSocket] = []
        
        # Building type mapping
        self.building_classes = {
            "Farm": Farm,
            "Market": Market,
            "School": School,
            "WoodcuttersCamp": WoodcuttersCamp,
            "Mine": Mine,
            "Library": Library,
            "Temple": Temple,
            "Housing": Housing,
            "Granary": Granary,
            "LumberYard": LumberYard,
            "University": University,
            "Hospital": Hospital,
        }
    
    def initialize(self):
        """Create new game using native classes (like starting new game in interactive_demo)."""
        logger.info("[*] Initializing game server (NATIVE GAME MODE)...")
        
        try:
            # Create world map
            self.worldmap = WorldMap(size=(100, 100))
            logger.info(f"    ✓ World map created (100x100)")
            
            # Create game instance
            self.game = Game(self.worldmap)
            logger.info(f"    ✓ Game initialized")
            
            # Create ideology
            ideology = NeutralIdeology()
            logger.info(f"    ✓ Neutral ideology created")
            
            # Create capital city (native City object)
            self.capital_city = City(gamenode=GameNode((0, 0), 5), size=5)
            self.capital_city.name = "Capitol"
            self.capital_city._resources.wealth = 100
            self.capital_city._resources.food = 100
            self.capital_city._resources.timber = 50
            self.capital_city._resources.metal = 50
            self.capital_city._societal_resources.population.add_population(500, 50)
            logger.info(f"    ✓ Capital city created")
            
            # Create empire (native Empire object)
            self.empire = Empire(autonomy=50, capital_city=self.capital_city, ideology=ideology)
            self.empire.name = "New Empire"
            self.empire.add_city(self.capital_city)
            self.all_cities.append(self.capital_city)
            self.game.add_empire(self.empire)
            logger.info(f"    ✓ Empire established")
            
            # Create additional cities
            city_configs = [
                {"name": "Harbor Town", "coords": (15, 20), "size": 4, "pop": 400, "wealth": 80, "food": 120, "timber": 30, "metal": 20},
                {"name": "Mountain Fort", "coords": (30, 35), "size": 4, "pop": 350, "wealth": 60, "food": 80, "timber": 20, "metal": 80},
                {"name": "Forest Village", "coords": (10, 40), "size": 3, "pop": 250, "wealth": 50, "food": 150, "timber": 100, "metal": 10},
            ]
            
            for config in city_configs:
                city = City(gamenode=GameNode(config["coords"], config["size"]), size=config["size"])
                city.name = config["name"]
                city._resources.wealth = config["wealth"]
                city._resources.food = config["food"]
                city._resources.timber = config["timber"]
                city._resources.metal = config["metal"]
                city._societal_resources.population.add_population(config["pop"], max(10, config["pop"] // 20))
                self.empire.add_city(city)
                self.all_cities.append(city)
                logger.info(f"    ✓ City created: {config['name']}")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize game: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        logger.info(f"[✓] Game server initialized successfully (NATIVE MODE) - {len(self.all_cities)} cities\n")
    
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
                        city = self.all_cities[self.selected_city_idx] if self.all_cities else self.capital_city
                        logger.info(f"[TICK {self.tick_count}] {city.name} Resources: "
                              f"F={city._resources.food:.0f}, "
                              f"T={city._resources.timber:.0f}, "
                              f"M={city._resources.metal:.0f}, "
                              f"W={city._resources.wealth:.0f}")
                        
                        # Log buildings
                        building_names = [b.__class__.__name__ for b in city._buildings]
                        logger.info(f"             Buildings: {building_names}")
                        logger.info(f"             Population: {city.total_population} ")
                        logger.info(f"             Game Events: {city.allegiance.game_events}")
                
                time.sleep(tick_interval)
            except Exception as e:
                logger.error(f"[ERROR] in tick loop: {e}")
                import traceback
                traceback.print_exc()
    
    def get_selected_city(self) -> City:
        """Get the currently selected city."""
        if not self.all_cities or self.selected_city_idx >= len(self.all_cities):
            return self.capital_city
        return self.all_cities[self.selected_city_idx]
    
    def select_city(self, city_id: int) -> Dict:
        """Select a city by index."""
        with self.lock:
            if city_id < 0 or city_id >= len(self.all_cities):
                raise ValueError(f"Invalid city ID: {city_id}")
            self.selected_city_idx = city_id
            city = self.all_cities[city_id]
            logger.info(f"[CITY SELECT] Switched to {city.name}")
            return {"status": "success", "city_id": city_id, "city_name": city.name}
    
    def get_cities_list(self) -> List[Dict]:
        """Get list of all cities with their basic info."""
        with self.lock:
            cities_data = []
            for i, city in enumerate(self.all_cities):
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
            if not self.all_cities or not self.empire:
                raise HTTPException(status_code=500, detail="Game not initialized")
            
            city = self.get_selected_city()
            
            # Extract population stats from native City object
            total_pop = city.total_population
            employable = city.employable_population
            employed = len([j for j in city._running_jobs if j is not None])
            
            # Extract buildings from native City object
            buildings = []
            for i, building in enumerate(city._buildings):
                building_data = BuildingData(
                    id=f"building_{i}",
                    name=building.__class__.__name__,
                    level=1,
                    space_used=building.size
                )
                buildings.append(building_data)
            
            # Extract resource capacities from native City object
            capacities = city.expendable_resource_capacities
            
            # Serialize city state
            city_state = CityStateData(
                coords=city.gamenode.coords,
                name=city.name if hasattr(city, 'name') else "Capital",
                population=PopulationData(
                    total=total_pop,
                    employable=employable,
                    employed=employed
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
                space_used=sum(b.size for b in city._buildings),
                space_total=city.size
            )
            
            # Serialize empire state
            empire_state = EmpireStateData(
                name=self.empire.name if hasattr(self.empire, 'name') else "Empire",
                knowledge=self.empire.knowledge,
                ideology=self.empire._ideology.__class__.__name__,
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
                )
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
                
                # Create native building object
                building_class = self.building_classes[building_type]
                building_job = CreationJob(building_class)
                city.add_job(building_job)
                # building = building_class()
                
                # Check space in native City object
                # space_used = sum(b.size for b in city._buildings)
                # if space_used + building.size > city.size:
                    # raise ValueError("Not enough space for building")
                
                # Get resource requirements from native building object
                # req: JobRequirements = building.job_requirements
                
                # if city._resources.wealth < req.wealth(level=1):
                    # raise ValueError("Not enough wealth resources")
                
                # Add to native City and deduct resources
                # city._buildings.append(building)
                # city._resources.wealth -= req.wealth(level=1)
                # city._resources.timber -= req.timber(level=1)
                
                logger.info(f"[BUILD] {building_type} being built in {city.name}")
                return {"status": "success", "building": building_type}
                
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
    """Perform action on a building."""
    if request.action == "demolish":
        result = game_server.demolish_building(request.building_id)
        return {
            "status": "success",
            "message": f"{result['building']} demolished"
        }
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")

@app.get("/api/buildings/available")
async def get_available_buildings():
    """Get list of available building types with construction requirements for level 1."""
    building_classes = [
        Farm, Market, School, WoodcuttersCamp, Mine, 
        Library, Temple, Housing, Granary, LumberYard,
        University, Hospital
    ]
    
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
        
        buildings.append({
            "name": building_class.name,
            "size": building_class.size,
            "description": building_class.description,
            "job_num_ticks": building_class.job_num_ticks,
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
        "empire_name": game_server.empire.name if game_server.empire else None,
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
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )