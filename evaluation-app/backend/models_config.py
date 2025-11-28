"""Configuration for available LLM models in the evaluation system.

Models are loaded from models.yaml (not committed to git).
Copy models.yaml.example to models.yaml and customise for your environment.
"""

import logging
from pathlib import Path
from typing import Literal, TypedDict

import yaml

logger = logging.getLogger(__name__)

# Valid reasoning effort levels supported by LiteLLM
ReasoningEffort = Literal["none", "low", "medium", "high"]


class ModelConfig(TypedDict, total=False):
    """Configuration for a single model."""

    id: str
    display_name: str
    provider: str | None
    # Reasoning/thinking configuration - model-agnostic via LiteLLM
    reasoning_effort: ReasoningEffort | None  # "none", "low", "medium", "high"
    # Whether the model supports reasoning_effort parameter (default: True)
    # Set to False for models that error with reasoning params (e.g., gpt-4o-mini)
    supports_reasoning: bool | None
    # Convert PDFs to images before sending to LLM (required for Azure-hosted OpenAI models)
    convert_pdf_to_images: bool | None


# Default fallback models if no config file exists
_DEFAULT_MODELS: list[ModelConfig] = [
    {
        "id": "gemini/gemini-2.0-flash",
        "display_name": "Gemini 2.0 Flash",
        "provider": "Google",
        "reasoning_effort": "low",
    },
]
_DEFAULT_MODEL_ID = "gemini/gemini-2.0-flash"

# Module-level cache for loaded config
_loaded_models: list[ModelConfig] | None = None
_loaded_default_id: str | None = None


def _get_config_path() -> Path:
    """Get path to models.yaml config file."""
    return Path(__file__).parent / "models.yaml"


def _load_config() -> tuple[list[ModelConfig], str]:
    """Load models configuration from YAML file.

    Returns:
        Tuple of (models list, default model ID)
    """
    global _loaded_models, _loaded_default_id

    if _loaded_models is not None:
        return _loaded_models, _loaded_default_id or _DEFAULT_MODEL_ID

    config_path = _get_config_path()

    if not config_path.exists():
        logger.warning(
            f"models.yaml not found at {config_path}. "
            "Using default configuration. "
            "Copy models.yaml.example to models.yaml to customise."
        )
        _loaded_models = _DEFAULT_MODELS
        _loaded_default_id = _DEFAULT_MODEL_ID
        return _loaded_models, _loaded_default_id

    try:
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if not config or "models" not in config:
            logger.warning("models.yaml is empty or missing 'models' key. Using defaults.")
            _loaded_models = _DEFAULT_MODELS
            _loaded_default_id = _DEFAULT_MODEL_ID
            return _loaded_models, _loaded_default_id

        models: list[ModelConfig] = []
        for model_data in config.get("models", []):
            model: ModelConfig = {
                "id": model_data.get("id", ""),
                "display_name": model_data.get("display_name", model_data.get("id", "")),
            }
            if "provider" in model_data:
                model["provider"] = model_data["provider"]
            if "reasoning_effort" in model_data:
                model["reasoning_effort"] = model_data["reasoning_effort"]
            if "supports_reasoning" in model_data:
                model["supports_reasoning"] = model_data["supports_reasoning"]
            if "convert_pdf_to_images" in model_data:
                model["convert_pdf_to_images"] = model_data["convert_pdf_to_images"]
            models.append(model)

        if not models:
            logger.warning("No models defined in models.yaml. Using defaults.")
            _loaded_models = _DEFAULT_MODELS
            _loaded_default_id = _DEFAULT_MODEL_ID
            return _loaded_models, _loaded_default_id

        _loaded_models = models
        _loaded_default_id = config.get("default_model", models[0]["id"])

        logger.info(f"Loaded {len(models)} models from {config_path}")
        return _loaded_models, _loaded_default_id

    except yaml.YAMLError as e:
        logger.error(f"Failed to parse models.yaml: {e}. Using defaults.")
        _loaded_models = _DEFAULT_MODELS
        _loaded_default_id = _DEFAULT_MODEL_ID
        return _loaded_models, _loaded_default_id


def get_available_models() -> list[ModelConfig]:
    """Get list of all available models."""
    models, _ = _load_config()
    return models


def get_default_model() -> ModelConfig:
    """Get the default model configuration."""
    models, default_id = _load_config()
    for model in models:
        if model["id"] == default_id:
            return model
    # Fallback to first model if default not found
    return models[0]


def get_model_by_id(model_id: str) -> ModelConfig | None:
    """Get a specific model by its ID."""
    models, _ = _load_config()
    for model in models:
        if model["id"] == model_id:
            return model
    return None


def reload_config() -> None:
    """Force reload of models configuration from file."""
    global _loaded_models, _loaded_default_id
    _loaded_models = None
    _loaded_default_id = None
    _load_config()
