from __future__ import annotations

import io
import json
import logging
from datetime import UTC, datetime
from typing import Any, cast

from planning_drawing_validator.types import RunID, StoragePrefix

from backend.services.document_service import UploadedFile
from backend.storage.client import StorageClient

logger = logging.getLogger(__name__)


def _get_database_models() -> tuple[Any, Any]:
    """Lazy import of database models to avoid circular imports."""
    from backend.database.connection import get_session_maker
    from backend.database.models import Run as DBRun

    return get_session_maker, DBRun


class RunMetadataService:
    """Manages run metadata in S3 and database."""

    def __init__(self, storage: StorageClient) -> None:
        self.storage = storage
        # Lazy import database to avoid circular dependency
        get_session_maker, self.DBRun = _get_database_models()
        self.Session = get_session_maker()

    def create_run_metadata(
        self,
        run_id: RunID,
        run_name: str,
        storage_prefix: StoragePrefix,
        uploaded_files: list[UploadedFile],
    ) -> dict[str, Any]:
        """Create comprehensive run metadata.

        Args:
            run_id: Unique run identifier
            run_name: Human-readable run name
            storage_prefix: S3 prefix for this run
            uploaded_files: List of uploaded file metadata

        Returns:
            Complete metadata dictionary
        """
        metadata = {
            "run_id": run_id,
            "run_name": run_name,
            "storage_prefix": storage_prefix,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
            "file_count": len(uploaded_files),
            "files": [
                {
                    "filename": f.filename,
                    "document_id": f.document_id,
                    "storage_key": f.storage_key,
                    "content_hash": f.content_hash,
                    "deduped": f.deduped,
                }
                for f in uploaded_files
            ],
            "ground_truth_path": None,
            "status": "created",
        }

        # Store in S3
        metadata_key = f"{storage_prefix}run_metadata.json"
        metadata_bytes = json.dumps(metadata, indent=2).encode("utf-8")
        self.storage.upload_fileobj(io.BytesIO(metadata_bytes), metadata_key)

        logger.info(f"Created run metadata in S3: {metadata_key}")
        return metadata

    def create_database_run(
        self,
        run_id: RunID,
        run_name: str,
        storage_prefix: StoragePrefix,
        file_count: int,
    ) -> None:
        """Create Run record in database.

        Args:
            run_id: Unique run identifier
            run_name: Human-readable run name
            storage_prefix: S3 prefix for this run
            file_count: Number of files in the run
        """
        with self.Session() as session:
            try:
                db_run = self.DBRun(
                    run_id=run_id,
                    name=run_name,
                    data_dir=storage_prefix,
                    status="created",
                    timestamp=datetime.now(UTC),
                    total_documents=file_count,
                    completed_documents=0,
                    execution_time=0.0,
                    ground_truth_path=None,
                    has_ground_truth=False,
                )
                session.add(db_run)
                session.commit()
                logger.info(f"Created Run record in database: {run_id}")
            except Exception as e:
                logger.error(f"Failed to create Run record in database: {e}", exc_info=True)
                session.rollback()
                # Don't fail the upload if database write fails - S3 metadata is source of truth
                raise

    @staticmethod
    def generate_run_id() -> tuple[RunID, str]:
        """Generate timestamped run ID and name with microsecond precision.

        Uses microseconds to ensure uniqueness even in rapid test execution.

        Returns:
            Tuple of (run_id, run_name)
        """
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S%f")
        run_id = f"run_{timestamp}"
        run_name = f"Run {timestamp}"
        return run_id, run_name


def get_run_metadata(storage_prefix: StoragePrefix, storage: StorageClient | None = None) -> dict[str, Any] | None:
    """Load run metadata from S3.

    Args:
        storage_prefix: S3 prefix for the run
        storage: Optional StorageClient instance. If not provided, creates one.

    Returns:
        Run metadata dictionary if found, None otherwise
    """
    try:
        from backend.storage.client import get_storage_client

        if storage is None:
            storage = get_storage_client()

        metadata_key = f"{storage_prefix.rstrip('/')}/run_metadata.json"
        content = storage.get_object(metadata_key)
        if content:
            return cast(dict[str, Any], json.loads(content.decode("utf-8")))
    except Exception as e:
        logger.warning(f"Failed to load run metadata from {storage_prefix}: {e}")
    return None


def update_run_metadata(
    storage_prefix: StoragePrefix,
    updates: dict[str, Any],
    storage: StorageClient | None = None,
) -> None:
    """Update specific fields in run metadata.

    Args:
        storage_prefix: S3 prefix for the run
        updates: Dictionary of fields to update
        storage: Optional StorageClient instance. If not provided, creates one.
    """
    from backend.storage.client import get_storage_client

    if storage is None:
        storage = get_storage_client()

    metadata = get_run_metadata(storage_prefix, storage) or {}
    metadata.update(updates)
    metadata["updated_at"] = datetime.now(UTC).isoformat()

    metadata_key = f"{storage_prefix.rstrip('/')}/run_metadata.json"
    metadata_bytes = json.dumps(metadata, indent=2).encode("utf-8")
    file_obj = io.BytesIO(metadata_bytes)
    file_obj.seek(0)  # Reset file pointer to beginning for upload
    storage.upload_fileobj(file_obj, metadata_key)
