"""
Database module for game persistence.

Provides:
- Database models (ORM)
- Persistence layer (save/load)
- Session management
- Game service
"""

from .config import DATABASE_URL, CURRENT_SCHEMA_VERSION, ENVIRONMENT
from .models import init_db, get_session_factory, Base
from .persistence import GamePersistence, GameService

__all__ = [
    "DATABASE_URL",
    "CURRENT_SCHEMA_VERSION",
    "ENVIRONMENT",
    "init_db",
    "get_session_factory",
    "Base",
    "GamePersistence",
    "GameService",
]