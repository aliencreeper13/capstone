"""
FastAPI Backend Server for Civilization Empire Builder Game
Provides REST API and WebSocket for real-time game updates.

Integrated with PostgreSQL for game state persistence.
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
from sqlalchemy.orm import Session

# Import game modules
import sys
sys.path.insert(0, r'c:\Users\MrCheese\Desktop\Programming\Python\capstone')

from backend.entities.city import City
from backend.entities.empire import Empire
from backend.entities.ideology import NeutralIdeology
from backend.gameplay.location import GameNode, WorldMap
from backend.gameplay.game import Game
from backend.systems.data import ExpendableCityResources

# Import database modules
from backend.database import (
    DATABASE_URL,
    CURRENT_SCHEMA_VERSION,
    ENVIRONMENT,
    init_db,
    get_session_factory,
    GameService,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
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
    building_type: str  # e.g., "Farm", "Market", etc.

class BuildingAction(BaseModel):
    building_id: str
    action: str  # "upgrade", "demolish"

# ============================================================================
# GAME SERVER
# ============================================================================

class GameServer:
    """Manages the game instance and auto-ticking with database persistence."""
    
    def __init__(self):
        self.game: Optional[Game] = None
        self.empire: Optional[Empire] = None
        self.capital_city: Optional[City] = None
        self.worldmap: Optional[WorldMap] = None
        self.is_running = False
        self.tick_count = 0
        self.building_id_counter = 0
        self.lock = threading.Lock()
        self.websocket_connections: List[WebSocket] = []
        
        # Database
        self.db_engine = None
        self.session_factory = None
        self.game_service: Optional[GameService] = None
        self.game_id: Optional[int] = None
        self.user_id: Optional[int] = 1  # Default user for now
        self.save_interval = 10  # Save every 10 ticks
        self.ticks_since_last_save = 0
    
    def init_database(self):
        """Initialize database connection."""
        try:
            logger.info(f"[*] Initializing database ({ENVIRONMENT})...")
            self.db_engine = init_db(DATABASE_URL)
            self.session_factory = get_session_factory(self.db_engine)
            logger.info(f"    ✓ Database initialized")
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize database: {e}")
            raise
    
    def initialize(self, game_id: Optional[int] = None, user_id: int = 1):
        """
        Initialize the game world.
        
        Args:
            game_id: If provided, load game from database. Otherwise create new game.
            user_id: User ID for the game.
        """
        logger.info("[*] Initializing game server...")
        
        self.user_id = user_id
        
        # Initialize database first
        if not self.db_engine:
            self.init_database()
        
        self.game_service = GameService(self.session_factory())
        
        try:
            if game_id:
                # Load game from database
                logger.info(f"[*] Loading game {game_id} from database...")
                self.game, self.empire, self.capital_city = self.game_service.load_game_state(game_id, user_id)
                self.worldmap = self.game.worldmap
                self.game_id = game_id
                logger.info(f"    ✓ Game loaded (tick {self.game.current_tick})")
            else:
                # Create new game
                logger.info("[*] Creating new game...")
                
                # Create world map
                self.worldmap = WorldMap(size=(100, 100))
                logger.info(f"    ✓ World map created (100x100)")
                
                # Create game instance
                self.game = Game(self.worldmap)
                logger.info(f"    ✓ Game ready")
                
                # Create ideology
                ideology = NeutralIdeology()
                logger.info(f"    ✓ Neutral ideology initialized")
                
                # Create capital city
                self.capital_city = City(gamenode=GameNode((0, 0), 5), size=5)
                self.capital_city.name = "Capitol"
                self.capital_city._resources.wealth = 100
                self.capital_city._resources.food = 100
                self.capital_city._resources.timber = 50
                self.capital_city._resources.metal = 50
                self.capital_city._societal_resources.population.add_population(500, 50)
                logger.info(f"    ✓ Capital city created")
                
                # Create empire
                self.empire = Empire(autonomy=50, capital_city=self.capital_city, ideology=ideology)
                self.empire.name = "New Empire"
                self.empire.add_city(self.capital_city)
                self.game.add_empire(self.empire)
                logger.info(f"    ✓ Empire established")
                
                # Save new game to database
                self.game_id = self.game_service.create_new_game(
                    user_id=user_id,
                    game_name="New Game",
                    worldmap_size=(100, 100)
                )
                self._save_game()
        
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize game: {e}")
            raise
        
        logger.info("[✓] Game server initialized successfully\n")
        
    def start_auto_tick(self):
        """Start the auto-ticking thread."""
        self.is_running = True
        self.tick_thread = threading.Thread(target=self._tick_loop, daemon=True)
        self.tick_thread.start()
        print("[*] Auto-tick thread started")
        
    def stop_auto_tick(self):
        """Stop the auto-ticking thread."""
        self.is_running = False
        
    def _tick_loop(self):
        """Main loop for auto-ticking the game."""
        tick_interval = 1.0  # 1 second per tick
        
        while self.is_running:
            try:
                with self.lock:
                    self.game.next_tick()
                    if self.capital_city:
                        # self.capital_city.update()
                        self.tick_count += 1
                        self.ticks_since_last_save += 1
                        
                        # Auto-save periodically
                        if self.ticks_since_last_save >= self.save_interval:
                            self._save_game()
                            self.ticks_since_last_save = 0
                        
                        if self.tick_count % 10 == 0:
                            logger.info(f"[TICK {self.tick_count}] Resources: "
                                  f"F={self.capital_city._resources.food:.0f}, "
                                  f"T={self.capital_city._resources.timber:.0f}, "
                                  f"M={self.capital_city._resources.metal:.0f}, "
                                  f"W={self.capital_city._resources.wealth:.0f}")
                            logger.info(f"Buildings: {[b.__class__.__name__ for b in self.capital_city._buildings]}")
                
                time.sleep(tick_interval)
            except Exception as e:
                logger.error(f"[ERROR] in tick loop: {e}")
    
    def _save_game(self):
        """Save current game state to database."""
        try:
            if self.game_service and self.game_id:
                self.game_service.save_game_state(
                    self.game_id,
                    self.user_id,
                    self.game,
                    self.empire,
                    self.capital_city
                )
                logger.info(f"[SAVE] Game state saved to database (tick {self.tick_count})")
        except Exception as e:
            logger.error(f"[ERROR] Failed to save game: {e}")
                
    def manual_save(self):
        """Manually save game state to database."""
        with self.lock:
            self._save_game()
    
    def get_game_state(self) -> GameStateResponse:
        """Get the current game state."""
        with self.lock:
            if not self.capital_city or not self.empire:
                raise HTTPException(status_code=500, detail="Game not initialized")
            
            city = self.capital_city
            
            # Calculate population stats
            total_pop = city.total_population
            employable = city.employable_population
            employed = len([j for j in city._running_jobs if j is not None])
            
            # Get buildings
            buildings = []
            for i, building in enumerate(city._buildings):
                building_data = BuildingData(
                    id=f"building_{i}",
                    name=building.__class__.__name__,
                    level=1,
                    space_used=building.size
                )
                buildings.append(building_data)
            
            # Calculate resource capacities
            capacities = city.expendable_resource_capacities
            
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
    
    def create_building(self, building_type: str):
        """Create a new building in the capital city."""
        from backend.entities.building import Building
        
        with self.lock:
            if not self.capital_city:
                raise HTTPException(status_code=500, detail="City not initialized")
            
            try:
                # Import building classes from interactive_demo
                import sys
                sys.path.insert(0, r'c:\Users\MrCheese\Desktop\Programming\Python\capstone')
                from interactive_demo import (
                    Farm, Market, School, WoodcuttersCamp, Mine, 
                    Library, Temple, Housing, Granary, LumberYard, 
                    University, Hospital
                )
                
                building_classes = {
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
                
                if building_type not in building_classes:
                    raise ValueError(f"Unknown building type: {building_type}")
                
                BuildingClass = building_classes[building_type]
                building = BuildingClass()
                
                # Check if there's enough space and resources
                space_used = sum(b.size for b in self.capital_city._buildings)
                if space_used + building.size > self.capital_city.size:
                    raise ValueError("Not enough space in city")
                
                # Check resources (simplified)
                req = building.job_requirements.expendable_city_resources_level1
                if (self.capital_city._resources.wealth < req.wealth or
                    self.capital_city._resources.timber < req.timber):
                    raise ValueError("Not enough resources")
                
                # Add building
                self.capital_city._buildings.append(building)
                
                # Deduct resources (simplified)
                self.capital_city._resources.wealth -= req.wealth
                self.capital_city._resources.timber -= req.timber
                
                return True
                
            except Exception as e:
                print(f"Error creating building: {e}")
                raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="Civilization Empire Builder", version="1.0.0")

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite dev server (if used)
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
    """Initialize the game on startup."""
    game_server.initialize(game_id=None, user_id=1)
    game_server.start_auto_tick()
    logger.info("[✓] Backend server started")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    game_server.stop_auto_tick()
    # Final save before shutdown
    game_server.manual_save()
    logger.info("[✓] Backend server stopped")

# ============================================================================
# REST API ENDPOINTS
# ============================================================================

@app.get("/api/game/state")
async def get_game_state():
    """Get the current game state."""
    return game_server.get_game_state()

@app.post("/api/building/create")
async def create_building(request: BuildingCreateRequest):
    """Create a new building."""
    game_server.create_building(request.building_type)
    return {"status": "success", "message": f"{request.building_type} created"}

@app.post("/api/building/action")
async def building_action(request: BuildingAction):
    """Perform an action on a building."""
    if request.action == "demolish":
        # Find and remove the building
        with game_server.lock:
            buildings = game_server.capital_city._buildings
            building_idx = int(request.building_id.split("_")[-1])
            if 0 <= building_idx < len(buildings):
                buildings.pop(building_idx)
                return {"status": "success", "message": "Building demolished"}
        raise HTTPException(status_code=404, detail="Building not found")
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")

@app.get("/api/buildings/available")
async def get_available_buildings():
    """Get list of available building types."""
    return {
        "buildings": [
            {"name": "Farm", "size": 1, "description": "Produces food"},
            {"name": "Market", "size": 3, "description": "Produces wealth"},
            {"name": "School", "size": 1, "description": "Produces knowledge"},
            {"name": "WoodcuttersCamp", "size": 3, "description": "Produces timber"},
            {"name": "Mine", "size": 1, "description": "Produces metal"},
            {"name": "Library", "size": 1, "description": "Increases morale"},
            {"name": "Temple", "size": 1, "description": "Increases morale"},
            {"name": "Housing", "size": 2, "description": "Increases population capacity"},
            {"name": "Granary", "size": 3, "description": "Increases food storage"},
            {"name": "LumberYard", "size": 3, "description": "Increases timber storage"},
            {"name": "University", "size": 4, "description": "Produces lots of knowledge"},
            {"name": "Hospital", "size": 4, "description": "Increases morale and lifespan"},
        ]
    }

# ============================================================================
# GAME PERSISTENCE ENDPOINTS
# ============================================================================

@app.post("/api/game/save")
async def save_game():
    """Manually save the current game state."""
    try:
        game_server.manual_save()
        return {
            "status": "success",
            "message": "Game saved successfully",
            "game_id": game_server.game_id,
            "tick": game_server.tick_count
        }
    except Exception as e:
        logger.error(f"Save error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/game/load/{game_id}")
async def load_game(game_id: int, user_id: int = 1):
    """Load a game from the database."""
    try:
        game_server.stop_auto_tick()
        game_server.initialize(game_id=game_id, user_id=user_id)
        game_server.start_auto_tick()
        return {
            "status": "success",
            "message": f"Game {game_id} loaded successfully",
            "game_id": game_id,
            "tick": game_server.tick_count
        }
    except Exception as e:
        logger.error(f"Load error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/game/info")
async def get_game_info():
    """Get current game information."""
    return {
        "game_id": game_server.game_id,
        "tick": game_server.tick_count,
        "status": "running" if game_server.is_running else "stopped",
        "environment": ENVIRONMENT,
        "schema_version": CURRENT_SCHEMA_VERSION
    }

# ============================================================================
# WEBSOCKET (future enhancement)
# ============================================================================

@app.websocket("/ws/game")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates (future enhancement)."""
    await websocket.accept()
    game_server.websocket_connections.append(websocket)
    
    try:
        while True:
            # Broadcast current game state every second
            state = game_server.get_game_state()
            await websocket.send_json(state.dict())
            await asyncio.sleep(1)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        game_server.websocket_connections.remove(websocket)

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "game_initialized": game_server.game is not None}

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("CIVILIZATION EMPIRE BUILDER - BACKEND SERVER")
    print("=" * 70 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )