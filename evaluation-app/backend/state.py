import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backend.config import EvaluationConfig, PathConfig

__all__ = ["AppState"]


@dataclass(slots=True)
class AppState:
    """Container for all application-level state.

    Manages configuration, concurrency control, data sources, and active evaluation state.
    Supports both local filesystem and S3 data sources.
    """

    # Configuration
    path_config: PathConfig
    database_url: str

    # Concurrency control
    doc_semaphore: asyncio.Semaphore = field(
        default_factory=lambda: asyncio.Semaphore(EvaluationConfig.DOC_SEMAPHORE_LIMIT)
    )

    # Current data source (either local path or S3 prefix)
    current_data_dir: Path | None = None
    current_storage_prefix: str | None = None

    # Active evaluation state
    current_evaluation: dict[str, Any] | None = None
    evaluation_task: asyncio.Task[Any] | None = None

    def __post_init__(self) -> None:
        """Initialise data directory from config if not set."""
        if self.current_data_dir is None:
            self.current_data_dir = self.path_config.data_dir

    def set_doc_concurrency(self, n: int | None) -> None:
        """Set document processing concurrency level.

        Args:
            n: Number of concurrent documents to process. Any positive integer.
                If None or invalid, defaults to configured semaphore limit.

        Note:
            Invalid values (non-positive, non-numeric) are silently converted to default
            to prevent runtime errors. Use logging to diagnose unexpected behaviour.
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            value = int(n) if n is not None else EvaluationConfig.DOC_SEMAPHORE_LIMIT
            if value <= 0:
                logger.warning(
                    f"Invalid concurrency value {value}, using default {EvaluationConfig.DOC_SEMAPHORE_LIMIT}"
                )
                value = EvaluationConfig.DOC_SEMAPHORE_LIMIT
        except (TypeError, ValueError) as e:
            logger.warning(
                f"Invalid concurrency value '{n}': {e}, using default {EvaluationConfig.DOC_SEMAPHORE_LIMIT}"
            )
            value = EvaluationConfig.DOC_SEMAPHORE_LIMIT

        self.doc_semaphore = asyncio.Semaphore(value)

    def reset_evaluation_state(self) -> None:
        """Clear all evaluation-related state.

        Resets current evaluation data and task reference.
        """
        self.current_evaluation = None
        self.evaluation_task = None

    def is_evaluation_running(self) -> bool:
        """Check if an evaluation is currently running.

        Returns:
            True if an evaluation task exists and is not done, False otherwise.
        """
        return self.evaluation_task is not None and not self.evaluation_task.done()

    def set_data_source_local(self, data_dir: Path) -> None:
        """Configure local filesystem as data source.

        Args:
            data_dir: Local directory path for document storage.
        """
        self.current_data_dir = data_dir
        self.current_storage_prefix = None

    def set_data_source_s3(self, storage_prefix: str, data_dir: Path | None = None) -> None:
        """Configure S3 as data source.

        Args:
            storage_prefix: S3 prefix for document storage.
            data_dir: Optional local data directory for metadata storage.
        """
        self.current_storage_prefix = storage_prefix
        if data_dir:
            self.current_data_dir = data_dir
