import os
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "PathConfig",
    "EvaluationConfig",
    "PaginationConfig",
    "StreamingConstants",
    "CacheConstants",
    "StorageConstants",
]


@dataclass(slots=True)
class PathConfig:
    """Configuration for file paths.

    Defines standard directory paths for data, prompts, and reports
    relative to the repository root.
    """

    base_dir: Path
    data_dir: Path
    prompts_dir: Path
    reports_dir: Path

    @classmethod
    def default(cls) -> "PathConfig":
        """Create default path configuration relative to repository root.

        Infers repository root as two levels above this file:
        backend/ → evaluation-app/ → repo root.

        Returns:
            PathConfig instance with standard directory paths.
        """
        backend_dir = Path(__file__).resolve().parent
        repo_root = backend_dir.parents[1]  # evaluation-app/ → repo root
        prompts_dir = (
            repo_root / "planning-drawing-validator" / "src" / "planning_drawing_validator" / "pipeline" / "prompts"
        )

        return cls(
            base_dir=repo_root,
            data_dir=repo_root / "data",
            prompts_dir=prompts_dir,
            reports_dir=repo_root / "reports",
        )

    def ensure_directories(self) -> None:
        """Create directories if they don't exist.

        Creates the reports directory. Other directories are expected to exist.
        """
        self.reports_dir.mkdir(exist_ok=True)


# ============================================================================
# Evaluation Configuration (Environment Variable Support)
# ============================================================================


class EvaluationConfig:
    """Configurable evaluation settings with environment variable support.

    Environment Variables:
        MAX_CONCURRENT_DOCUMENTS: Maximum concurrent document evaluations (default: 3)
        DOC_SEMAPHORE_LIMIT: Global document processing limit (default: 10)
        REQUEST_TIMEOUT_MS: Evaluation request timeout in milliseconds (default: 120000)
    """

    MAX_CONCURRENT_DOCUMENTS = int(os.getenv("MAX_CONCURRENT_DOCUMENTS", "3"))
    """Maximum number of documents to evaluate concurrently."""

    DOC_SEMAPHORE_LIMIT = int(os.getenv("DOC_SEMAPHORE_LIMIT", "10"))
    """Global application-level document processing concurrency limit."""

    REQUEST_TIMEOUT_MS = int(os.getenv("REQUEST_TIMEOUT_MS", "120000"))
    """Default timeout for evaluation requests (2 minutes)."""


class PaginationConfig:
    """Configurable pagination defaults with environment variable support.

    Environment Variables:
        DEFAULT_PAGE_LIMIT: Default number of items per page (default: 100)
        MAX_PAGE_LIMIT: Maximum allowed items per page (default: 1000)
    """

    DEFAULT_LIMIT = int(os.getenv("DEFAULT_PAGE_LIMIT", "100"))
    """Default number of items to return when limit not specified."""

    MAX_LIMIT = int(os.getenv("MAX_PAGE_LIMIT", "1000"))
    """Maximum number of items that can be requested in a single page."""


class StreamingConstants:
    """File streaming and chunking configuration.

    These values are optimised for network performance and should not be
    changed without performance testing.
    """

    CHUNK_SIZE_BYTES = 65536  # 64KB
    """
    Chunk size for streaming file uploads/downloads.

    64KB is optimal for most network conditions - balances memory usage
    with transfer efficiency. Larger chunks reduce overhead but increase
    memory pressure; smaller chunks increase overhead but reduce latency.
    """


class CacheConstants:
    """HTTP cache control headers for document responses."""

    DOCUMENT_CACHE_MAX_AGE = 3600  # 1 hour
    """Cache-Control max-age for document responses (in seconds)."""

    DOCUMENT_CACHE_CONTROL = f"public, max-age={DOCUMENT_CACHE_MAX_AGE}"
    """Full Cache-Control header value for document responses."""


class StorageConstants:
    """S3 storage path prefixes and structure."""

    S3_PREFIX_RUNS = "runs"
    """S3 prefix for evaluation run data."""

    S3_PREFIX_DOCUMENTS = "documents"
    """S3 prefix for document storage (content-addressable by hash)."""
