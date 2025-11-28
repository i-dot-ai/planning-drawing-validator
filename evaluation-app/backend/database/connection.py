import logging
import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.database.models import Base

__all__ = [
    "get_engine",
    "get_session_maker",
    "init_db",
    "drop_all_tables",
    "check_database_health",
    "dispose_engine",
]

logger = logging.getLogger(__name__)

# Database configuration from environment
DATABASE_URL = os.getenv("DATABASE_URL")
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "data/review.db")
USE_SQLITE = os.getenv("USE_SQLITE", "").lower() in ("true", "1", "yes")

# Connection pool configuration
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
POOL_MAX_OVERFLOW = int(os.getenv("DB_POOL_MAX_OVERFLOW", "10"))
POOL_RECYCLE_SECONDS = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1 hour
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))  # 30 seconds

# Global engine cache (singleton pattern)
_engine: Engine | None = None
_engine_url: str | None = None


def get_engine(database_url: str | None = None) -> Engine:
    """Get or create database engine using singleton pattern.

    Uses SQLite if USE_SQLITE environment variable is set, otherwise PostgreSQL.
    Database type must be explicitly configured - no automatic fallback.

    The engine is cached globally and reused across calls for efficiency.
    Connection pooling is configured via environment variables.

    Args:
        database_url: Optional database URL override. If not provided, uses
            DATABASE_URL environment variable.

    Returns:
        SQLAlchemy Engine instance configured for the selected database.

    Raises:
        Exception: If PostgreSQL connection fails and SQLite is not enabled.

    Note:
        SQLite automatically creates tables on first connection.
        PostgreSQL requires manual schema initialisation via init_db().
    """
    global _engine, _engine_url

    # Return cached engine if URL matches
    if database_url is None and _engine is not None:
        return _engine

    if USE_SQLITE:
        sqlite_path = Path(SQLITE_DB_PATH)
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)

        sqlite_url = f"sqlite:///{sqlite_path}"

        # Check if we need to create a new engine
        if _engine is None or _engine_url != sqlite_url:
            # Dispose old engine if exists
            if _engine is not None:
                _engine.dispose()

            engine = create_engine(
                sqlite_url,
                echo=False,
                # SQLite doesn't use connection pooling in the same way
                # StaticPool is better for SQLite with threading
                poolclass=None,  # Use default NullPool for SQLite
                connect_args={
                    "check_same_thread": False,  # Multi-threaded access
                    "timeout": POOL_TIMEOUT,  # Connection timeout
                },
            )
            logger.info(f"Using SQLite database: {sqlite_path}")

            # Auto-create tables for SQLite
            Base.metadata.create_all(engine)
            logger.info("SQLite tables created/verified")

            # Cache the engine
            _engine = engine
            _engine_url = sqlite_url

        return _engine

    # Use PostgreSQL (production/Docker environment)
    url = database_url or DATABASE_URL

    # Validate DATABASE_URL is set
    if not url:
        raise ValueError(
            "DATABASE_URL environment variable must be set when USE_SQLITE is false. "
            "Example: postgresql://user:password@localhost:5432/dbname"  # pragma: allowlist secret
        )

    # Check if we need to create a new engine
    if _engine is None or _engine_url != url:
        # Dispose old engine if exists
        if _engine is not None:
            _engine.dispose()

        engine = create_engine(
            url,
            echo=False,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=POOL_SIZE,  # Maximum pool size
            max_overflow=POOL_MAX_OVERFLOW,  # Allow temporary overflow connections
            pool_recycle=POOL_RECYCLE_SECONDS,  # Recycle connections after this many seconds
            pool_timeout=POOL_TIMEOUT,  # Timeout for getting connection from pool
        )

        # Test the connection
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(
                f"Connected to PostgreSQL: {url.split('@')[-1] if '@' in url else 'database'} "
                f"(pool_size={POOL_SIZE}, max_overflow={POOL_MAX_OVERFLOW})"
            )
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            logger.error("If running locally without Docker, set USE_SQLITE=true environment variable")
            raise

        # Cache the engine
        _engine = engine
        _engine_url = url

    return _engine


def get_session_maker(database_url: str | None = None) -> sessionmaker[Session]:
    """Get session maker for creating database sessions.

    Args:
        database_url: Optional database URL override.

    Returns:
        SQLAlchemy sessionmaker configured with the database engine.
    """
    engine = get_engine(database_url)
    return sessionmaker(bind=engine, expire_on_commit=False)


def init_db(database_url: str | None = None) -> None:
    """Initialise database schema.

    Creates all tables defined in the Base metadata. Safe to call multiple times -
    will only create missing tables.

    Args:
        database_url: Optional database URL override.

    Note:
        For SQLite, this is called automatically by get_engine().
        For PostgreSQL, must be called explicitly before first use.
    """
    engine = get_engine(database_url)
    Base.metadata.create_all(engine)


def drop_all_tables(database_url: str | None = None) -> None:
    """Drop all tables from the database.

    Args:
        database_url: Optional database URL override.

    Warning:
        This permanently deletes all data. Use with extreme caution.
        Intended for testing and development only.
    """
    engine = get_engine(database_url)
    Base.metadata.drop_all(engine)


def check_database_health(database_url: str | None = None) -> dict[str, bool | str]:
    """Check database connectivity and health.

    Performs basic connectivity tests and reports database status.
    Useful for health check endpoints and monitoring.

    Args:
        database_url: Optional database URL override.

    Returns:
        Dictionary with health status:
            - 'healthy': bool indicating overall health
            - 'message': str with status details
            - 'database_type': str ('sqlite' or 'postgresql')

    Example:
        >>> health = check_database_health()
        >>> if health['healthy']:
        >>>     print("Database is healthy")
    """
    try:
        engine = get_engine(database_url)

        # Test connection with a simple query
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()

        db_type = "sqlite" if USE_SQLITE else "postgresql"

        return {
            "healthy": True,
            "message": f"{db_type.capitalize()} database is accessible",
            "database_type": db_type,
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "healthy": False,
            "message": f"Database health check failed: {str(e)}",
            "database_type": "unknown",
        }


def dispose_engine() -> None:
    """Dispose of the cached database engine.

    Closes all connections in the pool and clears the engine cache.
    Primarily used for testing and cleanup scenarios.

    Warning:
        After calling this, the next call to get_engine() will create
        a new engine instance.
    """
    global _engine, _engine_url

    if _engine is not None:
        logger.info("Disposing database engine and clearing connection pool")
        _engine.dispose()
        _engine = None
        _engine_url = None
