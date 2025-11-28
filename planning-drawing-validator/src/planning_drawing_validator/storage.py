import logging
from pathlib import Path
from typing import Protocol, runtime_checkable

__all__ = [
    "ReadOnlyStorageProtocol",
    "ReadWriteStorageProtocol",
    "LocalFileSystemStorage",
]

logger = logging.getLogger(__name__)


@runtime_checkable
class ReadOnlyStorageProtocol(Protocol):
    """Protocol defining read-only storage operations for document validation.

    This is the minimal interface required by the document validator. It only needs
    to READ documents, not write or delete them. Keeping this protocol minimal allows
    for read-only implementations (caches, archives, CDNs, etc.) without forcing them
    to implement write operations.

    Applications can implement this protocol to provide custom storage backends
    (S3, Azure Blob, Google Cloud Storage, etc.). The core validator will work
    with any implementation that conforms to this interface.

    This is a structural protocol - implementations don't need to explicitly
    inherit from this class, they just need to implement the required methods.
    """

    def get_document(self, identifier: str) -> bytes:
        """Retrieve document content by identifier.

        Args:
            identifier: Storage-specific document identifier (e.g., file path for local storage,
                object key for S3, blob path for Azure, etc.)

        Returns:
            Document content as bytes.

        Raises:
            FileNotFoundError: If document doesn't exist.
            Exception: For other storage errors.
        """
        ...

    def document_exists(self, identifier: str) -> bool:
        """Check if a document exists.

        Args:
            identifier: Document identifier to check.

        Returns:
            True if document exists, False otherwise.
        """
        ...

    def find_document(self, prefix: str, filename: str) -> str | None:
        """Find a document by filename within a prefix/directory.

        Args:
            prefix: Prefix/directory to search within.
            filename: Filename to find.

        Returns:
            Full identifier (path/key) if found, None otherwise.
        """
        ...

    def list_documents(self, prefix: str, pattern: str = "*") -> list[str]:
        """List all documents matching a pattern within a prefix.

        Args:
            prefix: Prefix/directory to search within.
            pattern: Glob pattern to match files (e.g., "*.txt", "*.pdf").

        Returns:
            List of document identifiers matching the pattern.
        """
        ...


@runtime_checkable
class ReadWriteStorageProtocol(ReadOnlyStorageProtocol, Protocol):
    """Protocol extending read-only storage with write and delete operations.

    This protocol is for applications that need to manage the full document lifecycle:
    uploading, retrieving, and deleting documents. The core validator does NOT require
    this protocol - it only needs ReadOnlyStorageProtocol.

    Use this protocol when:
    - Building document management systems
    - Implementing upload APIs
    - Managing document cleanup/deletion
    - Building document caches with eviction

    Do NOT use this for the validator - it only needs read operations.
    """

    def write_document(self, identifier: str, content: bytes) -> None:
        """Write document content to storage.

        Args:
            identifier: Storage-specific identifier where to write (e.g., file path for local
                storage, object key for S3, blob path for Azure, etc.)
            content: Document content as bytes.

        Raises:
            Exception: For storage write errors.
        """
        ...

    def delete_document(self, identifier: str) -> None:
        """Delete a document from storage.

        Args:
            identifier: Document identifier to delete.

        Raises:
            FileNotFoundError: If document doesn't exist.
            Exception: For other storage errors.
        """
        ...


class LocalFileSystemStorage:
    """Default storage implementation using local filesystem.

    Provides document access from the local filesystem. This is the default
    storage backend provided by the core package, requiring no additional
    dependencies or configuration.

    Attributes:
        base_dir: Base directory for resolving relative paths.
    """

    def __init__(self, base_dir: Path | None = None):
        """Initialise local filesystem storage.

        Args:
            base_dir: Optional base directory for resolving relative paths.
                If not provided, uses current working directory.
        """
        self.base_dir = base_dir or Path.cwd()

    def get_document(self, identifier: str) -> bytes:
        """Retrieve document content from local filesystem.

        Args:
            identifier: File path (absolute or relative to base_dir).

        Returns:
            Document content as bytes.

        Raises:
            FileNotFoundError: If file doesn't exist or is not a file.
        """
        path = Path(identifier)

        # Try as absolute path first
        if path.is_absolute():
            if not path.exists() or not path.is_file():
                raise FileNotFoundError(f"File not found: {identifier}")
            return path.read_bytes()

        # Try relative to base_dir
        resolved_path = self.base_dir / path
        if not resolved_path.exists() or not resolved_path.is_file():
            raise FileNotFoundError(f"File not found: {identifier} (resolved: {resolved_path})")

        return resolved_path.read_bytes()

    def document_exists(self, identifier: str) -> bool:
        """Check if a document exists in local filesystem.

        Args:
            identifier: File path to check.

        Returns:
            True if file exists and is a file, False otherwise.
        """
        path = Path(identifier)

        # Try as absolute path
        if path.is_absolute():
            return path.exists() and path.is_file()

        # Try relative to base_dir
        resolved_path = self.base_dir / path
        return resolved_path.exists() and resolved_path.is_file()

    def find_document(self, prefix: str, filename: str) -> str | None:
        """Find a document by filename within a directory.

        Searches for the file first as a direct child, then recursively
        through all subdirectories if not found.

        Args:
            prefix: Directory path to search within.
            filename: Filename to locate.

        Returns:
            Full file path if found, None otherwise.
        """
        search_dir = Path(prefix)

        # Make absolute relative to base_dir if needed
        if not search_dir.is_absolute():
            search_dir = self.base_dir / search_dir

        if not search_dir.exists() or not search_dir.is_dir():
            logger.warning(f"Search directory does not exist: {search_dir}")
            return None

        # Try direct path first
        candidate = search_dir / filename
        if candidate.exists() and candidate.is_file():
            return str(candidate)

        # Search recursively
        try:
            for file_path in search_dir.rglob(filename):
                if file_path.is_file():
                    return str(file_path)
        except Exception as e:
            logger.error(f"Error searching for {filename} in {search_dir}: {e}")

        return None

    def list_documents(self, prefix: str, pattern: str = "*") -> list[str]:
        """List all documents matching a pattern within a directory.

        Args:
            prefix: Directory path to search within.
            pattern: Glob pattern to match files (e.g., "*.txt", "*.pdf").

        Returns:
            List of file paths matching the pattern.
        """
        search_dir = Path(prefix)

        # Make absolute relative to base_dir if needed
        if not search_dir.is_absolute():
            search_dir = self.base_dir / search_dir

        if not search_dir.exists() or not search_dir.is_dir():
            logger.warning(f"Search directory does not exist: {search_dir}")
            return []

        # Search recursively for matching files
        try:
            matches = []
            for file_path in search_dir.rglob(pattern):
                if file_path.is_file():
                    matches.append(str(file_path))
            return matches
        except Exception as e:
            logger.error(f"Error listing documents in {search_dir} with pattern {pattern}: {e}")
            return []

    def write_document(self, identifier: str, content: bytes) -> None:
        """Write document content to local filesystem.

        Args:
            identifier: File path (absolute or relative to base_dir).
            content: Document content as bytes.

        Raises:
            Exception: For filesystem write errors.
        """
        path = Path(identifier)

        # Resolve relative paths
        if not path.is_absolute():
            path = self.base_dir / path

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        path.write_bytes(content)

    def delete_document(self, identifier: str) -> None:
        """Delete a document from local filesystem.

        Args:
            identifier: File path to delete.

        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        path = Path(identifier)

        # Try as absolute path first
        if path.is_absolute():
            if not path.exists():
                raise FileNotFoundError(f"File not found: {identifier}")
            path.unlink()
            return

        # Try relative to base_dir
        resolved_path = self.base_dir / path
        if not resolved_path.exists():
            raise FileNotFoundError(f"File not found: {identifier} (resolved: {resolved_path})")
        resolved_path.unlink()
