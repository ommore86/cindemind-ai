"""
CineMind AI — Database Schema Initialization
Creates database tables safely if they do not exist.
"""

import logging
from app.database.connection import engine
from app.database.models import Base

logger = logging.getLogger("CineMind-DBInit")


def init_db():
    """Create tables safely without dropping existing data."""
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")


def auto_seed_if_empty(db):
    """
    If tables are empty (e.g. fresh deployment without committed SQLite file),
    auto-seeds from processed data artifacts without human intervention.
    """
    import os
    import importlib.util
    from app.database.models import Movie
    
    try:
        if db.query(Movie).count() > 0:
            return
            
        logger.info("Auto-seeding empty database from processed CSV artifacts...")
        candidates = [
            os.path.join("data", "processed"),
            os.path.join("..", "data", "processed"),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "processed"))
        ]
        processed_dir = None
        for c in candidates:
            if os.path.exists(os.path.join(c, "movies_processed.csv")):
                processed_dir = c
                break
                
        if not processed_dir:
            logger.warning("Could not locate processed data directory for auto-seeding.")
            return

        seed_script_candidates = [
            os.path.join("scripts", "seed_database.py"),
            os.path.join("..", "scripts", "seed_database.py"),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts", "seed_database.py"))
        ]
        for s_path in seed_script_candidates:
            if os.path.exists(s_path):
                spec = importlib.util.spec_from_file_location("seed_database_mod", s_path)
                seed_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(seed_mod)
                seed_mod.seed_database(processed_dir=processed_dir, max_ratings=110000)
                logger.info("Auto-seeding completed successfully.")
                return
    except Exception as e:
        logger.error(f"Auto-seeding encounter: {e}")


if __name__ == "__main__":
    init_db()
