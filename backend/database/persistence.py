"""
Game state persistence layer.

Handles saving and loading game state from the database.
Bridges domain objects (Empire, City, etc.) to ORM models.
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session

from backend.database import models
from backend.entities.empire import Empire
from backend.entities.city import City
from backend.entities.building import Building
from backend.entities.unit import Unit
from backend.entities.ideology import NeutralIdeology
from backend.systems.data import ExpendableEmpireResources, ExpendableCityResources, Population, SocietalResources
from backend.systems.effects import EffectWithTicksLeft
from backend.gameplay.game import Game
from backend.gameplay.location import WorldMap, GameNode

logger = logging.getLogger(__name__)


class GamePersistence:
    """Handles game persistence operations."""
    
    @staticmethod
    def save_game(
        session: Session,
        game_obj: Game,
        empire: Empire,
        city: City,
        game_id: int,
        user_id: int
    ) -> None:
        """
        Save game state to database.
        
        Args:
            session: SQLAlchemy session
            game_obj: The Game instance
            empire: The Empire instance
            city: The City instance
            game_id: Database game ID
            user_id: Database user ID
        """
        try:
            # Load or create DB records
            db_game = session.query(models.Game).filter_by(game_id=game_id).first()
            if not db_game:
                raise ValueError(f"Game {game_id} not found in database")
            
            # Update game tick
            db_game.current_tick = game_obj.current_tick
            db_game.last_modified_at = datetime.utcnow()
            
            # Save empire
            GamePersistence._save_empire(session, empire, game_id, user_id)
            
            # Save cities
            GamePersistence._save_city(session, city, empire.empire_id)
            
            session.commit()
            logger.info(f"[*] Game {game_id} saved successfully at tick {game_obj.current_tick}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"[ERROR] Failed to save game {game_id}: {e}")
            raise
    
    @staticmethod
    def _save_empire(session: Session, empire: Empire, game_id: int, user_id: int) -> None:
        """Save empire data."""
        db_empire = session.query(models.Empire).filter_by(game_id=game_id, owner_user_id=user_id).first()
        
        if not db_empire:
            db_empire = models.Empire(
                game_id=game_id,
                owner_user_id=user_id,
                name=empire.name,
                ideology_type=empire.ideology.__class__.__name__
            )
            session.add(db_empire)
            session.flush()
        
        # Update empire state
        db_empire.name = empire.name
        db_empire.knowledge = empire.knowledge
        db_empire.autonomy = empire.autonomy
        
        # Save resources
        total_resources = {
            "food": empire._resources.food,
            "timber": empire._resources.timber,
            "metal": empire._resources.metal,
            "wealth": empire._resources.wealth
        }
        db_empire.total_resources = total_resources
        db_empire.version += 1
        db_empire.last_modified_at = datetime.utcnow()
    
    @staticmethod
    def _save_city(session: Session, city: City, empire_id: int) -> None:
        """Save city data."""
        # Check if city already exists in DB
        db_city = session.query(models.City).filter_by(
            empire_id=empire_id,
            coord_x=city.gamenode.coords[0],
            coord_y=city.gamenode.coords[1]
        ).first()
        
        if not db_city:
            db_city = models.City(
                empire_id=empire_id,
                coord_x=city.gamenode.coords[0],
                coord_y=city.gamenode.coords[1],
                name=city.name
            )
            session.add(db_city)
            session.flush()
        
        # Update city state
        db_city.name = city.name
        db_city.is_capital = city.is_capital if hasattr(city, 'is_capital') else False
        
        # Resources
        db_city.resources = {
            "food": city._resources.food,
            "timber": city._resources.timber,
            "metal": city._resources.metal,
            "wealth": city._resources.wealth
        }
        db_city.resource_capacities = {
            "food": city.expendable_resource_capacities.food,
            "timber": city.expendable_resource_capacities.timber,
            "metal": city.expendable_resource_capacities.metal,
            "wealth": city.expendable_resource_capacities.wealth
        }
        
        # Population
        db_city.total_population = city.total_population
        db_city.employable_population = city.employable_population
        employed = len([j for j in city._running_jobs if j is not None])
        db_city.employed_population = employed
        
        # City state
        db_city.morale = city.morale
        db_city.defense = city.defense
        db_city.hitpoints = city.hitpoints
        db_city.max_hitpoints = city.max_hitpoints
        
        # Space
        db_city.space_used = city.space_used
        db_city.space_total = city.space_total
        
        db_city.version += 1
        db_city.last_modified_at = datetime.utcnow()
        
        # Save buildings
        GamePersistence._save_buildings(session, city, db_city.city_id)
        
        # Save active effects
        GamePersistence._save_effects(session, city, db_city.city_id)
    
    @staticmethod
    def _save_buildings(session: Session, city: City, db_city_id: int) -> None:
        """Save building instances."""
        # Clear old buildings
        session.query(models.BuildingInstance).filter_by(city_id=db_city_id).delete()
        
        # Save current buildings
        for building in city._buildings:
            db_building = models.BuildingInstance(
                city_id=db_city_id,
                building_id=building.__class__.__name__.lower(),
                level=getattr(building, 'level', 1),
                current_state={}
            )
            session.add(db_building)
    
    @staticmethod
    def _save_effects(session: Session, city: City, db_city_id: int) -> None:
        """Save active effects."""
        # Clear old effects
        session.query(models.ActiveEffect).filter_by(city_id=db_city_id).delete()
        
        # Save current effects
        for effect_with_ticks in city._effects_with_ticks_left:
            if effect_with_ticks:
                db_effect = models.ActiveEffect(
                    city_id=db_city_id,
                    effect_type=effect_with_ticks.effect.__class__.__name__,
                    effect_data={
                        "magnitude": getattr(effect_with_ticks.effect, 'magnitude', 0)
                    },
                    ticks_remaining=effect_with_ticks.ticks_left
                )
                session.add(db_effect)
    
    @staticmethod
    def load_game(
        session: Session,
        game_id: int,
        user_id: int
    ) -> tuple[Game, Empire, City]:
        """
        Load game state from database.
        
        Args:
            session: SQLAlchemy session
            game_id: Database game ID
            user_id: Database user ID
            
        Returns:
            Tuple of (Game, Empire, City) objects
        """
        try:
            # Load game
            db_game = session.query(models.Game).filter_by(game_id=game_id).first()
            if not db_game:
                raise ValueError(f"Game {game_id} not found")
            
            # Load empire
            db_empire = session.query(models.Empire).filter_by(
                game_id=game_id,
                owner_user_id=user_id
            ).first()
            if not db_empire:
                raise ValueError(f"Empire not found for game {game_id}")
            
            # Load city
            db_city = session.query(models.City).filter_by(
                empire_id=db_empire.empire_id
            ).first()
            if not db_city:
                raise ValueError(f"City not found for empire {db_empire.empire_id}")
            
            # Reconstruct domain objects
            empire = GamePersistence._load_empire(db_empire)
            city = GamePersistence._load_city(db_city, empire)
            
            # Create game and world map
            worldmap_size = db_game.worldmap_size
            worldmap = WorldMap(size=(worldmap_size['width'], worldmap_size['height']))
            
            game = Game(worldmap)
            game._current_tick = db_game.current_tick
            game.add_empire(empire)
            
            logger.info(f"[*] Game {game_id} loaded from database (tick {db_game.current_tick})")
            
            return game, empire, city
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to load game {game_id}: {e}")
            raise
    
    @staticmethod
    def _load_empire(db_empire: models.Empire) -> Empire:
        """Reconstruct Empire from database."""
        ideology = NeutralIdeology()  # Default ideology
        
        # Create empty empire (will be populated after city is loaded)
        empire = Empire(autonomy=db_empire.autonomy, capital_city=None, ideology=ideology)
        empire.name = db_empire.name
        empire.knowledge = db_empire.knowledge
        
        # Set resources
        resources = db_empire.total_resources
        empire._resources.food = resources.get('food', 0)
        empire._resources.timber = resources.get('timber', 0)
        empire._resources.metal = resources.get('metal', 0)
        empire._resources.wealth = resources.get('wealth', 0)
        
        return empire
    
    @staticmethod
    def _load_city(db_city: models.City, empire: Empire) -> City:
        """Reconstruct City from database."""
        # Create game node
        gamenode = GameNode(
            coords=(db_city.coord_x, db_city.coord_y),
            region_size=5
        )
        
        # Create city
        city = City(gamenode=gamenode, size=db_city.space_total)
        city.name = db_city.name
        city.is_capital = db_city.is_capital
        
        # Restore resources
        resources = db_city.resources
        city._resources.food = resources.get('food', 100)
        city._resources.timber = resources.get('timber', 50)
        city._resources.metal = resources.get('metal', 50)
        city._resources.wealth = resources.get('wealth', 100)
        
        # Restore population
        city._societal_resources.population._population = db_city.total_population
        city._societal_resources.population._employable_citizens = db_city.employable_population
        
        # Restore city state
        city.morale = db_city.morale
        city.defense = db_city.defense
        city.hitpoints = db_city.hitpoints
        city.max_hitpoints = db_city.max_hitpoints
        city.space_used = db_city.space_used
        
        # Set city allegiance to empire
        city._empire = empire
        
        return city


class GameService:
    """High-level service for game operations."""
    
    def __init__(self, db_session):
        self.session = db_session
    
    def create_new_game(
        self,
        user_id: int,
        game_name: str,
        worldmap_size: tuple = (100, 100)
    ) -> int:
        """Create a new game in the database."""
        game = models.Game(
            owner_user_id=user_id,
            game_name=game_name,
            worldmap_size={"width": worldmap_size[0], "height": worldmap_size[1]}
        )
        self.session.add(game)
        self.session.commit()
        
        logger.info(f"[*] New game created: {game_name} (ID: {game.game_id})")
        return game.game_id
    
    def save_game_state(
        self,
        game_id: int,
        user_id: int,
        game_obj: Game,
        empire: Empire,
        city: City
    ) -> None:
        """Save current game state."""
        GamePersistence.save_game(
            self.session,
            game_obj,
            empire,
            city,
            game_id,
            user_id
        )
    
    def load_game_state(
        self,
        game_id: int,
        user_id: int
    ) -> tuple[Game, Empire, City]:
        """Load game state from database."""
        return GamePersistence.load_game(self.session, game_id, user_id)
    
    def get_user_games(self, user_id: int) -> list:
        """Get all games for a user."""
        return self.session.query(models.Game).filter_by(owner_user_id=user_id).all()