from typing import Any

from pydantic import BaseModel

__all__ = [
    "ColumnConfig",
    "EvaluationRequest",
    "ResumeRequest",
    "GroundTruthPathRequest",
    "SaveGroundTruthRequest",
    "UpdateDocumentGroundTruthRequest",
    "PromptUpdateRequest",
    "ActivateVersionRequest",
    "SnapshotRequest",
    "RunUpdateRequest",
    "BulkDeleteRequest",
]


class ColumnConfig(BaseModel):
    """Configuration for ground truth file column names."""

    filename: str | None = None  # Column name for document filename
    validity: str | None = None  # Column name for validity label (VALID/INVALID)
    reason: str | None = None  # Column name for reasoning/explanation


class EvaluationRequest(BaseModel):
    """Request schema for starting a new evaluation run."""

    max_samples: int | None = None
    concurrency: int | None = None
    data_dir: str | None = None
    document_ids: list[str] | None = None
    skip_ground_truth: bool = False
    ground_truth_path: str | None = None
    model_name: str | None = None
    reasoning_effort: str | None = None  # "none", "low", "medium", "high" - overrides model default
    column_config: ColumnConfig | None = None  # Custom column names for ground truth file


class ResumeRequest(BaseModel):
    """Request schema for resuming a previously started evaluation run."""

    concurrency: int | None = None


class GroundTruthPathRequest(BaseModel):
    """Request schema for loading ground truth from a specific path."""

    ground_truth_path: str


class SaveGroundTruthRequest(BaseModel):
    """Request schema for saving ground truth entries to a file."""

    data_dir: str | None
    entries: list[dict[str, Any]]


class UpdateDocumentGroundTruthRequest(BaseModel):
    """Request schema for updating ground truth label for a single document."""

    document_id: str
    expected_validity: str
    run_id: str | None = None  # Optional run_id for updating historical runs


class PromptUpdateRequest(BaseModel):
    """Request schema for updating a prompt with new content."""

    content: str
    author: str = "user"
    description: str = "Updated prompt"
    metadata: dict[str, Any] | None = None


class ActivateVersionRequest(BaseModel):
    """Request schema for activating a specific prompt version."""

    update_filesystem: bool = True


class SnapshotRequest(BaseModel):
    """Request schema for creating a snapshot of prompt state."""

    author: str = "system"
    description: str = "Manual snapshot"


class RunUpdateRequest(BaseModel):
    """Request schema for updating run metadata."""

    name: str | None = None


class BulkDeleteRequest(BaseModel):
    """Request schema for bulk deleting multiple runs."""

    run_ids: list[str]
