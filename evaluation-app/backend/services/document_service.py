from __future__ import annotations

import hashlib
import io
import logging
import mimetypes
from collections.abc import Generator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from planning_drawing_validator.exceptions import DocumentNotFoundError
from planning_drawing_validator.storage import LocalFileSystemStorage
from planning_drawing_validator.types import (
    ContentHash,
    DocumentID,
    Filename,
    MimeType,
    RunID,
    StorageKey,
    StoragePrefix,
)
from sqlalchemy import select

from backend.config import StreamingConstants
from backend.storage.client import StorageClient

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from backend.database.models import StoredFile


def _get_database_models() -> tuple[Any, Any]:
    """Lazy import of database models to avoid circular imports."""
    from backend.database.connection import get_session_maker
    from backend.database.models import StoredFile

    return get_session_maker, StoredFile


@dataclass(slots=True)
class UploadedFile:
    """Metadata for an uploaded file.

    Uses __slots__ for memory efficiency.
    """

    filename: Filename
    content_hash: ContentHash
    storage_key: StorageKey
    file_size: int
    deduped: bool
    document_id: DocumentID


@dataclass(slots=True)
class DocumentInfo:
    """Information about a document for serving.

    Uses __slots__ for memory efficiency.
    """

    resolved_filename: Filename
    mime_type: MimeType
    size: int
    storage_key: StorageKey | None = None
    local_path: Path | None = None


class FileUploader:
    """Handles file upload with deduplication."""

    def __init__(self, storage: StorageClient, run_id: RunID):
        self.storage = storage
        self.run_id = run_id
        # Lazy import database to avoid circular dependency
        get_session_maker, self.StoredFile = _get_database_models()
        self.Session = get_session_maker()

    def _compute_hash(self, content: bytes) -> ContentHash:
        """Compute SHA256 hash of file content."""
        return hashlib.sha256(content).hexdigest()

    def _check_existing_file(self, content_hash: ContentHash, storage_key: StorageKey) -> Any | None:
        """Check if file with this hash already exists and verify storage object exists."""
        with self.Session() as session:
            stmt = select(self.StoredFile).where(self.StoredFile.content_hash == content_hash)
            existing_file = session.scalars(stmt).first()

            if not existing_file:
                return None

            # Verify storage object actually exists
            obj_content = self.storage.get_object(storage_key)
            if obj_content is None:
                logger.warning(f"Database claims file exists but storage object missing for {storage_key}")
                return None

            logger.info(f"File already exists in storage with hash {content_hash}, reusing")
            return existing_file

    def _create_database_record(
        self,
        content_hash: ContentHash,
        filename: Filename,
        storage_key: StorageKey,
        file_size: int,
        mime_type: MimeType | None,
    ) -> None:
        """Create database record for uploaded file."""
        with self.Session() as session:
            stored_file = self.StoredFile(
                content_hash=content_hash,
                original_filename=filename,
                storage_key=storage_key,
                file_size=file_size,
                mime_type=mime_type,
                run_id=self.run_id,
                file_category="document",
                uploaded_at=datetime.now(UTC),
                access_count=1,
            )
            session.add(stored_file)
            session.commit()

    def _update_existing_file_access(self, existing_file: StoredFile) -> None:
        """Update access counters for existing file."""
        with self.Session() as session:
            # Merge the existing file object with the current session
            existing_file = session.merge(existing_file)
            existing_file.access_count += 1
            existing_file.last_accessed_at = datetime.now(UTC)
            session.commit()

    def upload_file(self, filename: Filename, content: bytes, mime_type: MimeType | None) -> UploadedFile:
        """Upload a single file with deduplication.

        Args:
            filename: Original filename
            content: File content bytes
            mime_type: MIME type of the file

        Returns:
            UploadedFile metadata
        """
        file_size = len(content)
        content_hash = self._compute_hash(content)
        file_ext = Path(filename).suffix.lower()
        storage_key = f"documents/{content_hash}{file_ext}"

        # Check if this exact file already exists in THIS run
        with self.Session() as session:
            stmt = select(self.StoredFile).where(
                self.StoredFile.run_id == self.run_id,
                self.StoredFile.content_hash == content_hash,
            )
            existing_in_run = session.scalars(stmt).first()

        if existing_in_run:
            # File already uploaded in this run - just return metadata
            logger.info(f"File {filename} already uploaded in this run (hash: {content_hash})")
            document_id = self._extract_document_id(filename)
            return UploadedFile(
                filename=filename,
                content_hash=content_hash,
                storage_key=storage_key,
                file_size=file_size,
                deduped=True,
                document_id=document_id,
            )

        # Check if file already exists in S3 from a previous run
        existing_file = self._check_existing_file(content_hash, storage_key)

        if existing_file:
            # File exists in another run, update access count and create new run record
            self._update_existing_file_access(existing_file)
            self._create_database_record(content_hash, filename, storage_key, file_size, mime_type)

            document_id = self._extract_document_id(filename)
            return UploadedFile(
                filename=filename,
                content_hash=content_hash,
                storage_key=storage_key,
                file_size=file_size,
                deduped=True,
                document_id=document_id,
            )

        # Upload new file to S3
        file_io = io.BytesIO(content)
        if not self.storage.upload_fileobj(file_io, storage_key):
            raise RuntimeError(f"Failed to upload {filename} to S3")

        # Create database record
        self._create_database_record(content_hash, filename, storage_key, file_size, mime_type)

        logger.info(f"Uploaded {filename} to S3 as {storage_key} (hash: {content_hash})")

        document_id = self._extract_document_id(filename)
        return UploadedFile(
            filename=filename,
            content_hash=content_hash,
            storage_key=storage_key,
            file_size=file_size,
            deduped=False,
            document_id=document_id,
        )

    @staticmethod
    def _extract_document_id(filename: Filename) -> DocumentID:
        """Extract document ID from filename (without directory and extension)."""
        filename_only = filename.split("/")[-1]
        return filename_only.rsplit(".", 1)[0] if "." in filename_only else filename_only


class DocumentResolver:
    """Resolves document locations and provides metadata."""

    def __init__(self, storage: StorageClient):
        self.storage = storage
        # Lazy import database to avoid circular dependency
        get_session_maker, self.StoredFile = _get_database_models()
        self.Session = get_session_maker()

    def resolve_document(
        self,
        filename: Filename,
        storage_prefix: StoragePrefix | None = None,
        data_dir: Path | None = None,
    ) -> DocumentInfo:
        """Resolve document location using optimised search strategy.

        Search strategy (ordered by speed):
        1. Database lookup (fastest - single indexed query)
        2. S3 prefix search (slower - requires listing objects)
        3. Local filesystem (slowest - requires recursive directory search)

        Args:
            filename: Document filename to find
            storage_prefix: S3 prefix to search in (optional, used if database lookup fails)
            data_dir: Local directory to search in (optional, used as last resort)

        Returns:
            DocumentInfo with resolved location and metadata

        Raises:
            DocumentNotFoundError: If document not found in any checked location
        """
        logger.debug(f"Resolving '{filename}' (storage_prefix={storage_prefix}, data_dir={data_dir})")
        checked_locations = []

        # Strategy 1: Database (fastest - O(1) indexed query)
        checked_locations.append("database")
        if db_key := self._find_in_database(filename):
            logger.debug(f"Found '{filename}' in database: {db_key}")
            return self._get_storage_document_info(db_key)

        # Strategy 2: S3 prefix search (slower - O(n) object listing)
        if storage_prefix:
            checked_locations.append(f"s3://{storage_prefix}")
            if storage_key := self.storage.find_document(storage_prefix, filename):
                logger.debug(f"Found '{filename}' in S3: {storage_key}")
                return self._get_storage_document_info(storage_key)

        # Strategy 3: Local filesystem (slowest - recursive directory search)
        if data_dir:
            checked_locations.append(f"local:{data_dir}")
            local_storage = LocalFileSystemStorage()
            if file_path_str := local_storage.find_document(str(data_dir), filename):
                file_path = Path(file_path_str)
                logger.debug(f"Found '{filename}' locally: {file_path}")
                return self._get_local_document_info(file_path)

        # Not found anywhere - fail with clear error
        raise DocumentNotFoundError(
            filename,
            details={
                "checked_locations": checked_locations,
                "storage_prefix": storage_prefix,
                "data_dir": str(data_dir) if data_dir else None,
            },
        )

    def _find_in_database(self, filename: Filename) -> StorageKey | None:
        """Find most recent file by filename in database."""
        with self.Session() as session:
            stmt = (
                select(self.StoredFile)
                .where(self.StoredFile.original_filename == filename)
                .order_by(self.StoredFile.uploaded_at.desc())
            )
            stored_file = session.scalars(stmt).first()
            if stored_file:
                logger.info(f"Found document in database: {stored_file.storage_key}")
                return stored_file.storage_key
        return None

    def _get_storage_document_info(self, storage_key: StorageKey) -> DocumentInfo:
        """Get document info from storage.

        Args:
            storage_key: Storage object key/identifier

        Returns:
            DocumentInfo with metadata

        Raises:
            DocumentNotFoundError: If storage object metadata cannot be retrieved
        """
        metadata = self.storage.get_object_metadata(storage_key)
        if not metadata:
            raise DocumentNotFoundError(
                storage_key,
                details={
                    "reason": "Storage object metadata not found",
                    "storage_key": storage_key,
                },
            )

        # Determine MIME type
        mime_type = metadata.get("content_type") or "application/octet-stream"
        if not mime_type or mime_type == "binary/octet-stream":
            mime_type, _ = mimetypes.guess_type(storage_key)
            if not mime_type:
                mime_type = "application/octet-stream"

        return DocumentInfo(
            resolved_filename=storage_key.split("/")[-1],
            mime_type=mime_type,
            size=metadata.get("content_length", 0),
            storage_key=storage_key,
        )

    def _get_local_document_info(self, file_path: Path) -> DocumentInfo:
        """Get document info from local file."""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "application/octet-stream"

        return DocumentInfo(
            resolved_filename=file_path.name,
            mime_type=mime_type,
            size=file_path.stat().st_size,
            local_path=file_path,
        )

    def get_document_stream(
        self,
        filename: Filename,
        storage_prefix: StoragePrefix | None = None,
        data_dir: Path | None = None,
    ) -> tuple[Any, MimeType, int, Filename]:
        """Get streaming generator for document content.

        Args:
            filename: Document filename
            storage_prefix: S3 prefix (for S3 storage)
            data_dir: Local directory (for local storage)

        Returns:
            Tuple of (generator, mime_type, size, resolved_filename)

        Raises:
            DocumentNotFoundError: If document cannot be found or streamed
        """
        # resolve_document will raise DocumentNotFoundError if not found
        doc_info = self.resolve_document(filename, storage_prefix, data_dir)

        if doc_info.storage_key:
            # Stream from storage
            streaming_body = self.storage.get_object_streaming_body(doc_info.storage_key)
            if not streaming_body:
                raise DocumentNotFoundError(
                    filename,
                    details={
                        "reason": "Failed to get storage streaming body",
                        "storage_key": doc_info.storage_key,
                    },
                )

            def storage_generator() -> Generator[bytes]:
                yield from streaming_body.iter_chunks(chunk_size=StreamingConstants.CHUNK_SIZE_BYTES)

            return (
                storage_generator(),
                doc_info.mime_type,
                doc_info.size,
                doc_info.resolved_filename,
            )

        elif doc_info.local_path:
            # Stream from local file
            local_path = doc_info.local_path  # Capture for type narrowing

            def file_generator() -> Generator[bytes]:
                with open(local_path, "rb") as file:
                    while chunk := file.read(StreamingConstants.CHUNK_SIZE_BYTES):
                        yield chunk

            return (
                file_generator(),
                doc_info.mime_type,
                doc_info.size,
                doc_info.resolved_filename,
            )

        # This should never happen since resolve_document ensures either storage_key or local_path
        raise DocumentNotFoundError(
            filename,
            details={"reason": "Document resolved but has neither S3 key nor local path"},
        )
