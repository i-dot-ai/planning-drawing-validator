"""rename s3_key to storage_key

Revision ID: b8f3e1d2c5a9
Revises: a720d3ca9f42
Create Date: 2025-10-30

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b8f3e1d2c5a9"  # pragma: allowlist secret
down_revision: str | None = "a720d3ca9f42"  # pragma: allowlist secret
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Rename s3_key column to storage_key for storage-agnostic terminology."""
    # Drop the index on the old column name
    op.drop_index("ix_stored_files_s3_key", table_name="stored_files")

    # Rename the column
    op.alter_column("stored_files", "s3_key", new_column_name="storage_key")

    # Recreate the index with the new column name
    op.create_index(
        op.f("ix_stored_files_storage_key"),
        "stored_files",
        ["storage_key"],
        unique=False,
    )


def downgrade() -> None:
    """Revert storage_key column back to s3_key."""
    # Drop the index on the new column name
    op.drop_index(op.f("ix_stored_files_storage_key"), table_name="stored_files")

    # Rename the column back
    op.alter_column("stored_files", "storage_key", new_column_name="s3_key")

    # Recreate the index with the old column name
    op.create_index("ix_stored_files_s3_key", "stored_files", ["s3_key"], unique=False)
