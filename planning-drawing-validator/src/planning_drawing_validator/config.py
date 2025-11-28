from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


_config_dir = Path(__file__).resolve().parent
_repo_root = _config_dir.parents[2]
_env_file = _repo_root / ".env"

if _env_file.exists():
    load_dotenv(_env_file)
else:
    load_dotenv()

__all__ = ["ModelConfig", "PathConfig", "get_config"]


@dataclass(slots=True)
class ModelConfig:
    """Configuration for the LLM model.

    Uses i-dot-ai-utilities for LiteLLM configuration via environment variables.
    All LLM settings are managed by IAI_LITELLM_* environment variables.
    """

    max_concurrent: int = 10  # Default concurrency, user can set any value

    def __post_init__(self) -> None:
        """Validate configuration values.

        Raises:
            ValueError: If configuration values are invalid.
        """
        # Validate max_concurrent
        if self.max_concurrent <= 0:
            raise ValueError(f"max_concurrent must be positive, got {self.max_concurrent}")


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

        Infers repository root as three levels above this file:
        planning_drawing_validator/ → src/ → planning-drawing-validator/ → repo root.

        Returns:
            PathConfig instance with standard directory paths.
        """
        utils_dir = Path(__file__).resolve().parent
        repo_root = utils_dir.parents[2]
        return cls(
            base_dir=repo_root,
            data_dir=repo_root / "data",
            prompts_dir=utils_dir / "pipeline" / "prompts",
            reports_dir=repo_root / "reports",
        )

    def ensure_directories(self) -> None:
        """Create directories if they don't exist.

        Creates the reports directory. Other directories are expected to exist.
        """
        self.reports_dir.mkdir(exist_ok=True)


def get_config() -> tuple[ModelConfig, PathConfig]:
    """Get complete application configuration.

    Returns:
        Tuple containing ModelConfig and PathConfig instances.
    """
    return ModelConfig(), PathConfig.default()
