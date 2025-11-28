from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

__all__ = [
    # Base responses
    "SuccessResponse",
    "StatusResponse",
    "ErrorDetail",
    # Evaluation responses
    "EvaluationStartResponse",
    "EvaluationStatusResponse",
    "CurrentRunResponse",
    "EvaluationRun",
    # Run responses
    "RunSummary",
    "RunListResponse",
    "RunDetailResponse",
    "RunEventsResponse",
    "RunUpdateResponse",
    "RunDeleteResponse",
    "RunsClearResponse",
    # Document responses
    "DocumentInfo",
    "DocumentListResponse",
    "UploadedFileInfo",
    "DocumentUploadResponse",
    "DocumentInfoResponse",
    # Ground truth responses
    "GroundTruthUploadResponse",
    "GroundTruthEntry",
    "GroundTruthDataResponse",
    "GroundTruthSaveResponse",
    "GroundTruthUpdateResponse",
    # Prompt responses
    "PromptSummary",
    "PromptListResponse",
    "PromptVersionInfo",
    "PromptDetailResponse",
    "PromptVersionResponse",
    "PromptUpdateResponse",
    "PromptDeleteResponse",
    "PromptActivateResponse",
    "PromptSnapshotResponse",
    "PromptBranchResponse",
    # Health responses
    "HealthCheckResponse",
    # Model responses
    "ModelInfo",
    "ModelsListResponse",
    # Model comparison stats
    "ModelStatistics",
    "ModelStatsResponse",
]


# Base Response Models
class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool = True
    message: str | None = None


class StatusResponse(BaseModel):
    """Generic status response."""

    status: str
    message: str


class ErrorDetail(BaseModel):
    """Error detail information."""

    detail: str


# Evaluation Response Models
class EvaluationStartResponse(BaseModel):
    """Response when starting an evaluation."""

    status: Literal["started"]
    message: str
    run_id: str
    total_documents: int
    model_name: str | None = None
    reasoning_effort: str | None = None


class EvaluationStatusResponse(BaseModel):
    """Response for evaluation status check."""

    status: Literal["idle", "running", "completed", "cancelled", "error"]
    message: str
    results_count: int | None = None
    error: str | None = None


class CurrentRunResponse(BaseModel):
    """Response for current running evaluation snapshot."""

    status: Literal["running"]
    run_id: str
    total_documents: int
    completed_documents: int
    current_document_id: str | None = None
    documents: list[dict[str, Any]]


class EvaluationRun(BaseModel):
    """Response model for evaluation run data.

    Contains complete information about an evaluation run including metrics,
    document results, and execution history.
    """

    run_id: str
    timestamp: datetime
    total_documents: int
    completed_documents: int
    error_count: int = 0
    processed_count: int = 0
    overall_accuracy: float | None = None
    execution_time: float
    status: str  # 'completed', 'cancelled', 'error', 'running'
    documents: list[dict[str, Any]]
    events: list[dict[str, Any]] | None = None
    name: str | None = None
    has_ground_truth: bool = False
    model_name: str | None = None
    reasoning_effort: str | None = None

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Convert to dictionary for JSON serialisation.

        Conditionally excludes accuracy metric when ground truth is not available.
        """
        result = super().model_dump(**kwargs)
        # Only include accuracy if ground truth is available
        if not self.has_ground_truth:
            result.pop("overall_accuracy", None)
        return result


# Run Response Models
class RunSummary(BaseModel):
    """Summary information for a single run in list view."""

    run_id: str
    name: str | None
    timestamp: str
    total_documents: int
    completed_documents: int
    error_count: int = 0
    processed_count: int = 0
    overall_accuracy: float
    execution_time: float
    status: str
    document_count: int
    model_name: str | None = None
    reasoning_effort: str | None = None

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Add aliases for frontend compatibility."""
        result = super().model_dump(**kwargs)
        # Add accuracy field as alias of overall_accuracy for frontend
        result["accuracy"] = result.get("overall_accuracy", 0.0)
        # Add start_time as alias of timestamp for frontend
        result["start_time"] = result.get("timestamp")
        return result


class RunListResponse(BaseModel):
    """Response containing list of evaluation runs."""

    runs: list[RunSummary]


class RunDetailResponse(BaseModel):
    """Response containing detailed run information with documents."""

    run_id: str
    timestamp: str
    total_documents: int
    completed_documents: int
    overall_accuracy: float
    execution_time: float
    status: str
    documents: list[dict[str, Any]]
    model_name: str | None = None
    reasoning_effort: str | None = None

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Add aliases for frontend compatibility."""
        result = super().model_dump(**kwargs)
        # Add accuracy field as alias of overall_accuracy for frontend
        result["accuracy"] = result.get("overall_accuracy", 0.0)
        # Add start_time as alias of timestamp for frontend
        result["start_time"] = result.get("timestamp")
        return result


class RunEventsResponse(BaseModel):
    """Response containing events for a specific run."""

    events: list[dict[str, Any]]


class RunUpdateResponse(BaseModel):
    """Response when updating run metadata."""

    status: Literal["updated"]
    run_id: str
    name: str | None


class RunDeleteResponse(BaseModel):
    """Response when deleting a run."""

    status: Literal["deleted"]
    message: str


class RunsClearResponse(BaseModel):
    """Response when clearing runs (all or specific)."""

    status: Literal["cleared", "deleted"]
    message: str


# Document Response Models
class DocumentInfo(BaseModel):
    """Information about a single document."""

    document_id: str
    filename: str


class DocumentListResponse(BaseModel):
    """Response containing list of documents."""

    documents: list[DocumentInfo]


class UploadedFileInfo(BaseModel):
    """Information about an uploaded file."""

    filename: str
    document_id: str
    content_hash: str
    storage_key: str
    deduped: bool


class DocumentUploadResponse(BaseModel):
    """Response when uploading documents."""

    success: bool = True
    data_dir: str
    storage_prefix: str
    run_id: str
    file_count: int
    run_name: str
    files: list[UploadedFileInfo]


class DocumentInfoResponse(BaseModel):
    """Response containing document metadata."""

    resolved_filename: str
    mime_type: str
    size: int
    url: str | None = None


# Ground Truth Response Models
class GroundTruthUploadResponse(BaseModel):
    """Response when uploading ground truth file."""

    success: bool = True
    ground_truth_path: str
    filename: str
    entries_count: int = 0


class GroundTruthEntry(BaseModel):
    """A single ground truth entry."""

    document_id: str
    filename: str
    expected_validity: str


class GroundTruthDataResponse(BaseModel):
    """Response containing ground truth entries."""

    success: bool = True
    entries: list[GroundTruthEntry]


class GroundTruthSaveResponse(BaseModel):
    """Response when saving ground truth."""

    success: bool = True
    ground_truth_path: str
    entries_count: int


class GroundTruthUpdateResponse(BaseModel):
    """Response when updating document ground truth."""

    success: bool = True
    message: str


# Prompt Response Models
class PromptSummary(BaseModel):
    """Summary information for a prompt."""

    name: str
    type: str
    version_count: int
    active_version: str | None


class PromptListResponse(BaseModel):
    """Response containing list of prompts."""

    prompts: list[dict[str, Any]]  # Keep flexible for now


class PromptVersionInfo(BaseModel):
    """Information about a prompt version."""

    version_id: str
    version_number: int
    timestamp: str
    author: str
    description: str
    is_active: bool
    parent_version_id: str | None
    metadata: dict[str, Any] | None


class PromptDetailResponse(BaseModel):
    """Response containing detailed prompt information."""

    name: str
    type: str
    current_content: str | None
    versions: list[PromptVersionInfo]
    active_version: dict[str, Any] | None


class PromptVersionResponse(BaseModel):
    """Response for a specific prompt version."""

    version_id: str
    prompt_name: str
    prompt_type: str
    content: str
    timestamp: str
    author: str
    description: str
    parent_version_id: str | None
    is_active: bool
    metadata: dict[str, Any] | None


class PromptUpdateResponse(BaseModel):
    """Response when updating a prompt."""

    status: Literal["updated"]
    version_id: str
    message: str


class PromptDeleteResponse(BaseModel):
    """Response when deleting a prompt version."""

    status: Literal["deleted"]
    version_id: str
    message: str


class PromptActivateResponse(BaseModel):
    """Response when activating a prompt version."""

    status: Literal["activated"]
    version_id: str
    message: str


class PromptSnapshotResponse(BaseModel):
    """Response when creating a snapshot."""

    status: Literal["snapshot_created", "snapshots_created"]
    version_id: str | None = None
    count: int | None = None
    message: str


class PromptBranchResponse(BaseModel):
    """Response when creating a branch from a version."""

    status: Literal["branch_created"]
    version_id: str
    parent_version_id: str
    message: str


# Health Response Models
class HealthCheckResponse(BaseModel):
    """Response for health check endpoint."""

    status: Literal["healthy"]
    service: str


# Model Response Models
class ModelInfo(BaseModel):
    """Information about a single model."""

    id: str
    display_name: str
    is_default: bool = False
    provider: str | None = None
    reasoning_effort: str | None = None  # "none", "low", "medium", "high"


class ModelsListResponse(BaseModel):
    """Response containing list of available models."""

    models: list[ModelInfo]


# Model Comparison Statistics
class ModelStatistics(BaseModel):
    """Aggregated statistics for a single model (optionally grouped by reasoning_effort)."""

    model_name: str
    reasoning_effort: str | None = None  # "none", "low", "medium", "high" - only set when grouping by effort
    run_count: int
    total_documents: int
    avg_accuracy: float | None
    min_accuracy: float | None
    max_accuracy: float | None
    std_accuracy: float | None
    avg_execution_time: float | None
    avg_precision: float | None
    avg_recall: float | None
    avg_f1_score: float | None
    avg_reasoning_accuracy: float | None = None  # Average of reasoning_match_score where evaluated
    reasoning_eval_count: int = 0  # Number of documents with reasoning evaluation
    latest_run_timestamp: str | None
    run_ids: list[str]


class ModelStatsResponse(BaseModel):
    """Response containing model comparison statistics."""

    model_stats: list[ModelStatistics]
