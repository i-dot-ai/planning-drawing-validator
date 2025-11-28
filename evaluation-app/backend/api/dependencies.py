import asyncio
import logging
import os
from collections.abc import Generator
from functools import lru_cache
from typing import Any

from planning_drawing_validator.config import get_config

from backend.database.connection import get_session_maker
from backend.prompt_manager import PromptManager
from backend.state import AppState
from backend.storage.client import StorageClient, get_storage_client

logger = logging.getLogger(__name__)

# Configuration
_, path_config = get_config()  # Still need GCP config from core package

# Database setup - lazy initialization for testability
_session_maker = None


def get_session_maker_instance() -> Any:
    """Get or create the session maker instance.

    Lazy-initialises the SessionMaker to allow test fixtures to override
    the database URL before the session maker is created.

    Returns:
        sessionmaker instance bound to the configured database
    """
    global _session_maker
    if _session_maker is None:
        DATABASE_URL = os.getenv("DATABASE_URL")
        if not DATABASE_URL:
            raise ValueError(
                "DATABASE_URL environment variable must be set. "
                "Example: postgresql://user:password@localhost:5432/dbname"  # pragma: allowlist secret
            )
        _session_maker = get_session_maker(DATABASE_URL)
    return _session_maker


def set_session_maker_for_tests(session_maker: Any) -> None:
    """Override the session maker for testing.

    This function is used by test fixtures to inject a test database session maker.

    Args:
        session_maker: Test session maker instance or None to reset
    """
    global _session_maker
    _session_maker = session_maker


def get_db_session() -> Generator[Any, None, None]:
    """FastAPI dependency for database sessions.

    Yields a new database session and ensures cleanup.
    Uses lazy-initialised session maker for testability.
    """
    SessionMaker = get_session_maker_instance()
    session = SessionMaker()
    try:
        yield session
    finally:
        session.close()


@lru_cache
def get_storage_client_cached() -> StorageClient:
    """Get or create singleton storage client instance.

    Uses functools.lru_cache for singleton behaviour following FastAPI best practices.
    The cached instance is reused across all requests for performance.

    For testing, override this dependency using:
        app.dependency_overrides[get_storage_client_cached] = lambda: MockStorageClient()

    Returns:
        Singleton StorageClient instance
    """
    logger.info("Initialising StorageClient singleton")
    return get_storage_client()


def get_storage() -> StorageClient:
    """FastAPI dependency for storage client.

    Returns cached singleton storage client instance.
    Delegates to get_storage_client_cached() for actual singleton management.

    Returns:
        Singleton StorageClient instance
    """
    return get_storage_client_cached()


@lru_cache
def get_prompt_manager_cached() -> PromptManager:
    """Get or create singleton prompt manager instance.

    Uses functools.lru_cache for singleton behaviour following FastAPI best practices.
    The cached instance is reused across all requests for performance.

    For testing, override this dependency using:
        app.dependency_overrides[get_prompt_manager_cached] = lambda: MockPromptManager()

    Returns:
        Singleton PromptManager instance
    """
    logger.info("Initialising PromptManager singleton")
    return PromptManager()


def get_prompt_manager() -> PromptManager:
    """FastAPI dependency for prompt manager.

    Returns cached singleton prompt manager instance.
    Delegates to get_prompt_manager_cached() for actual singleton management.

    Returns:
        Singleton PromptManager instance
    """
    return get_prompt_manager_cached()


def get_app_state() -> AppState:
    """FastAPI dependency for application state.

    Returns the global application state instance.
    """
    return app_state


# Application-level document concurrency semaphore
# Controls how many documents are processed in parallel across the app
DOC_SEMAPHORE: asyncio.Semaphore | None = None


def set_doc_concurrency(n: int | None) -> None:
    """Set global document processing concurrency limit."""
    global DOC_SEMAPHORE
    if n and n > 0:
        DOC_SEMAPHORE = asyncio.Semaphore(n)
    else:
        DOC_SEMAPHORE = None


# Global app state instance using the centralised AppState from core.state
# Use lazy evaluation for DATABASE_URL to support testing
app_state = AppState(
    path_config=path_config,
    database_url=os.getenv("DATABASE_URL", "sqlite:///:memory:"),
)

# Initialise semaphore with default value
set_doc_concurrency(10)
