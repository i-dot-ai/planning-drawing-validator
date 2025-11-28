import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from planning_drawing_validator.llm.protocol import LLMProtocol

__all__ = ["get_llm_client", "dispose_llm_client"]

logger = logging.getLogger(__name__)


@dataclass
class _ClientCache:
    """Cache for LLM client instance"""

    client: "LLMProtocol"
    model: str


_cache: _ClientCache | None = None


def get_llm_client(model_name: str | None = None) -> "LLMProtocol":
    """Get or create cached LLM client instance using i-dot-ai-utilities.

    Returns cached client if model matches, otherwise creates a new LiteLLM client.
    By default uses IAI_LITELLM_CHAT_MODEL from environment, but can be overridden.

    Args:
        model_name: Optional model name override. If provided, overrides
                   IAI_LITELLM_CHAT_MODEL environment variable.
                   Useful for testing different models or dynamic model selection.

    Returns:
        LiteLLM client instance conforming to LLMProtocol.

    Raises:
        ImportError: If i-dot-ai-utilities package is not installed.

    Examples:
        # Use default model from IAI_LITELLM_CHAT_MODEL env var
        client = get_llm_client()

        # Override with specific model
        client = get_llm_client(model_name="openai/gpt-4o")
    """
    global _cache

    effective_model = model_name if model_name else "configured-via-env"

    # Return cached client if model matches
    if _cache and _cache.model == effective_model:
        return _cache.client

    # Dispose old client if exists (model changed)
    if _cache:
        logger.info(f"Disposing LLM client: model={_cache.model}")

    # Create new LiteLLM client
    logger.info(f"Creating LiteLLM client: model={effective_model}")

    from planning_drawing_validator.llm.litellm_client import LiteLLMClient

    client = LiteLLMClient(model_name=model_name)

    # Cache the new client
    _cache = _ClientCache(client=client, model=effective_model)
    logger.info(f"LiteLLM client created: model={effective_model}")

    return client


def dispose_llm_client() -> None:
    """Dispose of the cached LLM client.

    Clears the client cache. Traces are managed automatically by i-dot-ai-utilities.
    Primarily used for testing and cleanup scenarios.

    Warning:
        After calling this, the next call to get_llm_client() will create
        a new client instance.
    """
    global _cache

    if _cache:
        logger.info(f"Disposing LLM client: model={_cache.model}")
        _cache = None
