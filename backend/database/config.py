"""
Database configuration for dev and production environments.
"""

import os
from typing import Optional
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

# Environment-based database URLs
DATABASE_DEV = os.getenv("DATABASE_DEV_URL", "postgresql://postgres:postgres@localhost:5432/empire_dev")
DATABASE_PROD = os.getenv("DATABASE_PROD_URL", "postgresql://postgres:postgres@localhost:5432/empire_prod")

# Get current environment
ENVIRONMENT = os.getenv("FLASK_ENV", "development")

# Select appropriate database
DATABASE_URL = DATABASE_PROD if ENVIRONMENT == "production" else DATABASE_DEV

# Connection pool settings
SQLALCHEMY_ECHO = ENVIRONMENT == "development"  # Log SQL in dev
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_MAX_OVERFLOW = 20
SQLALCHEMY_POOL_TIMEOUT = 30
SQLALCHEMY_POOL_RECYCLE = 3600  # Recycle connections every hour

# Schema versioning
CURRENT_SCHEMA_VERSION = 1

print(f"[*] Database config loaded (Environment: {ENVIRONMENT})")
print(f"    Database URL: {DATABASE_URL.split('@')[-1]}")  # Only print the host part