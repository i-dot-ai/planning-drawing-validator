import logging
import os
import sys
import warnings

__all__ = ["setup_logging"]

_LEVELS = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


def _coerce_level(level: str | None) -> int:
    if isinstance(level, str):
        return _LEVELS.get(level.upper(), logging.INFO)
    return logging.INFO


def setup_logging(level: str | None = None) -> None:
    """Configure application logging with sensible defaults.

    Sets up a StreamHandler writing to stdout with timestamp formatting.
    Suppresses verbose third-party library logging from Vertex AI SDK.

    Log level priority:
        1. Explicit level argument
        2. LOG_LEVEL environment variable
        3. INFO (default)

    Args:
        level: Log level string (CRITICAL, ERROR, WARNING, INFO, DEBUG).
            If None, uses LOG_LEVEL environment variable or INFO.
    """
    env_level = os.getenv("LOG_LEVEL")
    effective_level = _coerce_level(level or env_level)

    root = logging.getLogger()
    # Avoid duplicate handlers when re-invoked (e.g., in notebooks)
    if root.handlers:
        for h in list(root.handlers):
            root.removeHandler(h)

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setLevel(effective_level)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )

    root.setLevel(effective_level)
    root.addHandler(handler)

    # Tidy up overly chatty libraries
    logging.getLogger("vertexai").setLevel(max(logging.WARNING, effective_level))

    warnings.filterwarnings(
        "ignore",
        category=UserWarning,
        module=r"vertexai\.generative_models\..*",
        message=r"This feature is deprecated.*genai-vertexai-sdk",
    )
