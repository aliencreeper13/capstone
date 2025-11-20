"""
SQLAlchemy ORM models for game persistence.

These models represent the database schema and map to game domain objects.
Following the hybrid approach: top-level entities (Empire, City) with full state,
and references to immutable templates (Building, Unit types) by ID.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    ForeignKey, Text, JSON, create_engine, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import QueuePool

Base = declarative_base()


# ============================================================================
# USER & GAME ACCESS
# ============================================================================

class User(Base):
    """User account model."""
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    auth_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    games = relationship("Game", back_populates="owner")
    game_participants = relationship("GameParticipant", back_populates="user")


class Game(Base):
    """Game/save file model."""
    __tablename__ = "games"
    
    game_id = Column(Integer, primary_key=True)
    owner_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    game_name = Column(String(255), nullable=False)
    status = Column(String(50), default="active", nullable=False)  # active/paused/completed
    current_tick = Column(Integer, default=0, nullable=False)
    schema_version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Game world data (stored as JSON for flexibility)
    worldmap_size = Column(JSON, nullable=False)  # {"width": 100, "height": 100}
    
    # Relationships
    owner = relationship("User", back_populates="games")
    empires = relationship("Empire", back_populates="game", cascade="all, delete-orphan")
    participants = relationship("GameParticipant", back_populates="game", cascade="all, delete-orphan")
    events = relationship("GameEvent", back_populates="game", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_game_owner_id", "owner_user_id"),
        Index("idx_game_created_at", "created_at"),
    )


class GameParticipant(Base):
    """Multiplayer access control for games."""
    __tablename__ = "game_participants"
    
    participant_id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.game_id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    permission_level = Column(String(50), default="editor", nullable=False)  # owner/editor/viewer
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    game = relationship("Game", back_populates="participants")
    user = relationship("User", back_populates="game_participants")
    
    __table_args__ = (
        Index("idx_participant_game_user", "game_id", "user_id"),
    )


# ============================================================================
# CORE GAME ENTITIES
# ============================================================================

class Empire(Base):
    """Empire model - player's civilization."""
    __tablename__ = "empires"
    
    empire_id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.game_id"), nullable=False, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, index=True)
    
    # Core state
    name = Column(String(255), nullable=False)
    knowledge = Column(Float, default=0, nullable=False)
    autonomy = Column(Float, default=50, nullable=False)
    ideology_type = Column(String(255), default="neutral", nullable=False)
    
    # Resources (aggregate)
    total_resources = Column(JSON, nullable=False, default=lambda: {
        "food": 0, "timber": 0, "metal": 0, "wealth": 0
    })
    
    # Metadata
    version = Column(Integer, default=1, nullable=False)  # For optimistic locking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    game = relationship("Game", back_populates="empires")
    cities = relationship("City", back_populates="empire", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_empire_game_id", "game_id"),
        Index("idx_empire_owner_id", "owner_user_id"),
    )


class City(Base):
    """City model - urban center within an empire."""
    __tablename__ = "cities"
    
    city_id = Column(Integer, primary_key=True)
    empire_id = Column(Integer, ForeignKey("empires.empire_id"), nullable=False, index=True)
    
    # Location
    coord_x = Column(Integer, nullable=False)
    coord_y = Column(Integer, nullable=False)
    
    # Basic info
    name = Column(String(255), nullable=False)
    is_capital = Column(Boolean, default=False, nullable=False)
    
    # Resources (mutable state)
    resources = Column(JSON, nullable=False, default=lambda: {
        "food": 100, "timber": 50, "metal": 50, "wealth": 100
    })
    resource_capacities = Column(JSON, nullable=False, default=lambda: {
        "food": 500, "timber": 300, "metal": 300, "wealth": 500
    })
    
    # Population (mutable state)
    total_population = Column(Integer, default=500, nullable=False)
    employable_population = Column(Integer, default=50, nullable=False)
    employed_population = Column(Integer, default=0, nullable=False)
    
    # City state
    morale = Column(Float, default=100, nullable=False)
    defense = Column(Float, default=100, nullable=False)
    hitpoints = Column(Float, default=100, nullable=False)
    max_hitpoints = Column(Float, default=100, nullable=False)
    
    # Space management
    space_used = Column(Integer, default=0, nullable=False)
    space_total = Column(Integer, default=25, nullable=False)
    
    # Metadata
    version = Column(Integer, default=1, nullable=False)  # For optimistic locking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    empire = relationship("Empire", back_populates="cities")
    buildings = relationship("BuildingInstance", back_populates="city", cascade="all, delete-orphan")
    units = relationship("UnitInstance", back_populates="city", cascade="all, delete-orphan")
    job_assignments = relationship("JobAssignment", back_populates="city", cascade="all, delete-orphan")
    active_effects = relationship("ActiveEffect", back_populates="city", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_city_empire_id", "empire_id"),
        Index("idx_city_coords", "coord_x", "coord_y"),
    )


# ============================================================================
# BUILDINGS & UNITS (HYBRID APPROACH)
# ============================================================================

class BuildingInstance(Base):
    """Instance of a building in a city (references template by ID)."""
    __tablename__ = "building_instances"
    
    instance_id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.city_id"), nullable=False, index=True)
    
    # Reference to building template (not a foreign key - it's immutable data)
    building_id = Column(String(255), nullable=False)  # e.g., "barracks", "farm"
    level = Column(Integer, default=1, nullable=False)
    
    # Current state of this instance
    current_state = Column(JSON, nullable=False, default=lambda: {})
    
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    city = relationship("City", back_populates="buildings")
    
    __table_args__ = (
        Index("idx_building_city_id", "city_id"),
        Index("idx_building_id", "building_id"),
    )


class UnitInstance(Base):
    """Active unit instance (soldiers, workers, settlers, etc.)."""
    __tablename__ = "unit_instances"
    
    unit_id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.city_id"), nullable=False, index=True)
    
    # Unit type reference
    unit_type_id = Column(String(255), nullable=False)
    
    # Combat state
    position = Column(JSON, nullable=False, default=lambda: {"x": 0, "y": 0})
    health = Column(Float, nullable=False)
    status = Column(String(50), default="idle", nullable=False)  # idle/moving/attacking
    
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    city = relationship("City", back_populates="units")
    
    __table_args__ = (
        Index("idx_unit_city_id", "city_id"),
        Index("idx_unit_type_id", "unit_type_id"),
    )


# ============================================================================
# EFFECTS & JOBS
# ============================================================================

class ActiveEffect(Base):
    """Active effect applied to a city or empire."""
    __tablename__ = "active_effects"
    
    effect_id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.city_id"), nullable=False, index=True)
    
    # Effect metadata
    effect_type = Column(String(255), nullable=False)  # e.g., "food_production_boost"
    effect_data = Column(JSON, nullable=False)  # Flexible data structure
    
    # Timing
    ticks_remaining = Column(Integer, nullable=True)  # None = permanent
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    city = relationship("City", back_populates="active_effects")
    
    __table_args__ = (
        Index("idx_effect_city_id", "city_id"),
        Index("idx_effect_expires", "ticks_remaining"),
    )


class JobAssignment(Base):
    """Job assignment for city workers."""
    __tablename__ = "job_assignments"
    
    assignment_id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("cities.city_id"), nullable=False, index=True)
    
    # Job details
    job_type = Column(String(255), nullable=False)
    job_data = Column(JSON, nullable=False, default=lambda: {})
    citizen_count = Column(Integer, default=1, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    city = relationship("City", back_populates="job_assignments")
    
    __table_args__ = (
        Index("idx_job_city_id", "city_id"),
        Index("idx_job_type", "job_type"),
    )


# ============================================================================
# GAME EVENTS & AUDIT TRAIL
# ============================================================================

class GameEvent(Base):
    """Historical game event log."""
    __tablename__ = "game_events"
    
    event_id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.game_id"), nullable=False, index=True)
    
    # Event metadata
    event_type = Column(String(255), nullable=False)  # e.g., "building_built", "war_declared"
    event_data = Column(JSON, nullable=False)  # Event-specific data
    
    triggered_by_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    order_index = Column(Integer, nullable=False)  # For replay capability
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    game = relationship("Game", back_populates="events")
    
    __table_args__ = (
        Index("idx_event_game_id", "game_id"),
        Index("idx_event_timestamp", "timestamp"),
        Index("idx_event_type", "event_type"),
    )


class ActionLog(Base):
    """Audit trail of user actions."""
    __tablename__ = "action_logs"
    
    action_id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.game_id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    
    # Action details
    action_type = Column(String(255), nullable=False)
    action_data = Column(JSON, nullable=False)
    
    # Status
    applied_to_db = Column(Boolean, default=False, nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("idx_action_game_id", "game_id"),
        Index("idx_action_user_id", "user_id"),
        Index("idx_action_timestamp", "timestamp"),
    )


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db(database_url: str):
    """Initialize database engine and create tables."""
    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600,
        echo=False
    )
    
    Base.metadata.create_all(engine)
    return engine


def get_session_factory(engine):
    """Create a session factory."""
    return sessionmaker(bind=engine, expire_on_commit=False)