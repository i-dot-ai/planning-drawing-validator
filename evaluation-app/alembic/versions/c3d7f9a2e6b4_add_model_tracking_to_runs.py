"""add model tracking to runs

Revision ID: c3d7f9a2e6b4
Revises: b8f3e1d2c5a9
Create Date: 2025-11-24

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d7f9a2e6b4"  # pragma: allowlist secret
down_revision: str | None = "b8f3e1d2c5a9"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add model_name and model_config columns to runs table for model tracking."""
    # Add model_name column
    op.add_column("runs", sa.Column("model_name", sa.String(200), nullable=True))

    # Add model_config column for storing additional parameters
    op.add_column("runs", sa.Column("model_config", sa.JSON(), nullable=True))

    # Create index on model_name for efficient grouping/filtering
    op.create_index(op.f("ix_runs_model_name"), "runs", ["model_name"], unique=False)


def downgrade() -> None:
    """Remove model tracking columns from runs table."""
    # Drop the index
    op.drop_index(op.f("ix_runs_model_name"), table_name="runs")

    # Drop the columns
    op.drop_column("runs", "model_config")
    op.drop_column("runs", "model_name")
