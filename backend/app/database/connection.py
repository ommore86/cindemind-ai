"""
CineMind AI — Database Connection & Session Management
Supports SQLite (local development fallback) and PostgreSQL (production).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
import logging

logger = logging.getLogger("CineMind-Database")

database_url = settings.DATABASE_URL
connect_args = {}

if database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
    prefix = "sqlite:///"
    if database_url.startswith(prefix):
        raw_path = database_url[len(prefix):]
        # If relative path, locate cinemind.db intelligently
        if not os.path.isabs(raw_path) and raw_path != ":memory:":
            clean_name = os.path.basename(raw_path) or "cinemind.db"
            candidates = [
                os.path.abspath(clean_name),
                os.path.abspath(os.path.join("..", clean_name)),
                os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", clean_name))
            ]
            for c in candidates:
                if os.path.exists(c):
                    database_url = f"sqlite:///{c}"
                    break
            else:
                # Default to repository root path if not found yet
                repo_root_db = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", clean_name))
                database_url = f"sqlite:///{repo_root_db}"

engine = create_engine(
    database_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI Dependency for database session management."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
