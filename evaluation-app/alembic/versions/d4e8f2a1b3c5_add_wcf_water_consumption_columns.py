"""add wcf water consumption columns

Revision ID: d4e8f2a1b3c5
Revises: c3d7f9a2e6b4
Create Date: 2025-11-28

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e8f2a1b3c5"  # pragma: allowlist secret
down_revision: str | None = "c3d7f9a2e6b4"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add wcf (water consumption factor) columns to document_results table."""
    op.add_column("document_results", sa.Column("carbon_wcf_l_min", sa.Float(), nullable=True))
    op.add_column("document_results", sa.Column("carbon_wcf_l_max", sa.Float(), nullable=True))


def downgrade() -> None:
    """Remove wcf columns from document_results table."""
    op.drop_column("document_results", "carbon_wcf_l_max")
    op.drop_column("document_results", "carbon_wcf_l_min")
