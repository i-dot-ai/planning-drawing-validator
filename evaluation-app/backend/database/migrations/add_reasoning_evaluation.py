"""Migration script to add reasoning evaluation columns to document_results table.

This migration adds columns for storing LLM-as-judge reasoning evaluation results:
- reasoning_match_score: Semantic match score (0.0-1.0)
- reasoning_evaluated: Whether reasoning evaluation was performed
- reasoning_explanation: Brief explanation of the match
- expected_reasoning: Ground truth reasoning for reference

Run this script to migrate an existing database:
    python -m backend.database.migrations.add_reasoning_evaluation
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
    """Add reasoning evaluation columns to document_results table if they don't exist."""
    engine = get_engine()

    columns_to_add = [
        ("reasoning_match_score", "FLOAT"),
        ("reasoning_evaluated", "BOOLEAN DEFAULT FALSE"),
        ("reasoning_explanation", "TEXT"),
        ("expected_reasoning", "TEXT"),
    ]

    with engine.connect() as conn:
        for column_name, column_type in columns_to_add:
            # Check if column already exists
            if column_exists(conn, "document_results", column_name):
                logger.info(f"Column '{column_name}' already exists in 'document_results' table")
                continue

            # Add the column
            try:
                conn.execute(text(f"ALTER TABLE document_results ADD COLUMN {column_name} {column_type}"))
                conn.commit()
                logger.info(f"Successfully added '{column_name}' column to 'document_results' table")
            except Exception as e:
                logger.error(f"Failed to add column '{column_name}': {e}")
                raise


if __name__ == "__main__":
    migrate()
