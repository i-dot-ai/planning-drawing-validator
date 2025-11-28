"""API router for model configuration endpoints."""

import logging
import os
from typing import Any

import httpx
from fastapi import APIRouter

from backend.api.models.responses import ModelInfo, ModelsListResponse
from backend.models_config import get_available_models, get_default_model

router = APIRouter(prefix="/api/models")
logger = logging.getLogger(__name__)


async def fetch_litellm_models() -> list[dict[str, Any]] | None:
    """Fetch models from LiteLLM proxy gateway.

    Queries the /models endpoint on the configured LiteLLM gateway
    to get the actual list of available models.

    Can be disabled by setting USE_STATIC_MODEL_CONFIG=true to use
    only the static configuration file.

    Returns:
        List of model dictionaries with id and display name, or None if fetch fails.
    """
    # Check if user wants to skip LiteLLM query and use static config only
    use_static = os.getenv("USE_STATIC_MODEL_CONFIG", "false").lower() == "true"
    if use_static:
        logger.info("USE_STATIC_MODEL_CONFIG=true, skipping LiteLLM query")
        return None

    api_base = os.getenv("IAI_LITELLM_API_BASE")
    if not api_base:
        logger.warning("IAI_LITELLM_API_BASE not configured, cannot query LiteLLM")
        return None

    try:
        # Query the LiteLLM /models endpoint
        url = f"{api_base.rstrip('/')}/models"
        logger.info(f"Querying LiteLLM models endpoint: {url}")

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()

            data = response.json()
            models = []

            # Parse OpenAI-compatible /models response format
            if "data" in data:
                for model_data in data["data"]:
                    model_id = model_data.get("id", "")
                    if model_id:
                        # Create a display name from the ID
                        display_name = model_id.replace("litellm_proxy/", "").replace("-", " ").title()
                        models.append({"id": model_id, "display_name": display_name})

            logger.info(f"Successfully fetched {len(models)} models from LiteLLM gateway")
            return models

    except httpx.TimeoutException:
        logger.warning(f"Timeout querying LiteLLM models endpoint: {url}")
        return None
    except httpx.HTTPError as e:
        logger.warning(f"HTTP error querying LiteLLM models: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error querying LiteLLM models: {e}", exc_info=True)
        return None


@router.get("", response_model=ModelsListResponse)
async def list_models() -> ModelsListResponse:
    """Get list of available models for evaluation.

    By default, queries the LiteLLM gateway for available models. Falls back
    to static configuration if the gateway is unavailable.

    Priority:
    1. Query LiteLLM gateway /models endpoint (unless USE_STATIC_MODEL_CONFIG=true)
    2. Use static config file as fallback

    Configuration:
    - Set USE_STATIC_MODEL_CONFIG=true to skip LiteLLM query and use only static config
    - IAI_LITELLM_API_BASE must be set for LiteLLM queries (also needed for LLM client)

    Returns all models with their display names and indicates which is default.
    """
    # Try to fetch from LiteLLM gateway first
    litellm_models = await fetch_litellm_models()

    # Use LiteLLM models if available, otherwise fall back to config
    if litellm_models:
        logger.info(f"Using {len(litellm_models)} models from LiteLLM gateway")
        models = litellm_models
    else:
        logger.info("Using models from static configuration")
        models = get_available_models()

    # Get default model from config
    default_model = get_default_model()
    default_id = default_model["id"]

    model_list = [
        ModelInfo(
            id=model["id"],
            display_name=model["display_name"],
            is_default=model["id"] == default_id,
            provider=model.get("provider"),
            reasoning_effort=model.get("reasoning_effort"),
        )
        for model in models
    ]

    return ModelsListResponse(models=model_list)
