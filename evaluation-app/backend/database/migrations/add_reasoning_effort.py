"""Migration script to add reasoning_effort column to runs table.

This migration adds a reasoning_effort column to track the thinking/reasoning
level used for each evaluation run.

Run this script to migrate an existing database:
    python -m backend.database.migrations.add_reasoning_effort
"""

import logging
import os
import sys

from sqlalchemy import text

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from backend.database.connection import get_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table (PostgreSQL and SQLite compatible)."""
    # Try PostgreSQL information_schema first
    try:
        result = conn.execute(
            text("SELECT 1 FROM information_schema.columns WHERE table_name = :table AND column_name = :column"),
            {"table": table_name, "column": column_name},
        )
        return result.fetchone() is not None
    except Exception:
        # Fallback for SQLite - use pragma
        try:
            result = conn.execute(text(f"PRAGMA table_info({table_name})"))
            columns = [row[1] for row in result.fetchall()]
            return column_name in columns
        except Exception:
            return False


def migrate():
    """Add reasoning_effort column to runs table if it doesn't exist."""
    engine = get_engine()

    with engine.connect() as conn:
        # Check if column already exists
        if column_exists(conn, "runs", "reasoning_effort"):
            logger.info("Column 'reasoning_effort' already exists in 'runs' table")
            return

        # Add the column
        try:
            conn.execute(text("ALTER TABLE runs ADD COLUMN reasoning_effort VARCHAR(20)"))
            conn.commit()
            logger.info("Successfully added 'reasoning_effort' column to 'runs' table")
        except Exception as e:
            logger.error(f"Failed to add column: {e}")
            raise


if __name__ == "__main__":
    migrate()
