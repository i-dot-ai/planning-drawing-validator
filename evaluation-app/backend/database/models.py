from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from backend.api.constants import RunStatus

__all__ = [
    "Base",
    "Run",
    "DocumentResult",
    "RunEvent",
    "RunEvaluation",
    "PromptVersion",
    "StoredFile",
]


class Base(DeclarativeBase):
    """Base class for all database models.

    Provides the declarative base that all ORM models inherit from.
    Uses SQLAlchemy 2.0 style declarative mapping.
    """


class Run(Base):
    """Stores high-level information about EVALUATION RUNS (QA testing).

    Each run represents an evaluation session processing test documents through
    the validator and comparing predictions to ground truth for performance measurement.

    This is part of the EVALUATION SYSTEM (not production validation).
    Production validation is stateless and does not require database storage.

    Evaluation runs track:
    - Performance metrics (accuracy, precision, recall)
    - Ground truth comparison results
    - Test dataset processing statistics
    - Quality assurance metrics over time

    Optimised for fast list queries - detailed results stored in separate tables.
    """

    __tablename__ = "runs"
    __table_args__ = (
        # Composite indexes for common query patterns
        Index("ix_runs_status_timestamp", "status", "timestamp"),
        Index("ix_runs_has_ground_truth_timestamp", "has_ground_truth", "timestamp"),
        # Additional indexes for query optimisation
        Index("ix_runs_status_ground_truth", "status", "has_ground_truth", "timestamp"),
        Index("ix_runs_timestamp_id", "timestamp", "id"),  # Pagination performance
        # Check constraints for data validation
        CheckConstraint("total_documents >= 0", name="ck_runs_total_documents_non_negative"),
        CheckConstraint("completed_documents >= 0", name="ck_runs_completed_documents_non_negative"),
        CheckConstraint(
            "completed_documents <= total_documents",
            name="ck_runs_completed_not_exceeds_total",
        ),
        CheckConstraint(
            "overall_accuracy IS NULL OR (overall_accuracy >= 0 AND overall_accuracy <= 1)",
            name="ck_runs_accuracy_range",
        ),
        CheckConstraint("execution_time >= 0", name="ck_runs_execution_time_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(200))  # User-defined run name
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    # Summary metrics
    total_documents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_documents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    execution_time: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=RunStatus.RUNNING.value
    )  # Use RunStatus enum: RUNNING, COMPLETED, CANCELLED, ERROR

    # Accuracy metrics (only when ground truth is provided)
    overall_accuracy: Mapped[float | None] = mapped_column(Float)
    has_ground_truth: Mapped[bool] = mapped_column(default=False)

    # Configuration
    data_dir: Mapped[str | None] = mapped_column(String(500))
    ground_truth_path: Mapped[str | None] = mapped_column(String(500))
    max_samples: Mapped[int | None] = mapped_column(Integer)
    concurrency: Mapped[int | None] = mapped_column(Integer)

    # Model tracking
    model_name: Mapped[str | None] = mapped_column(String(200), index=True)  # LiteLLM model identifier
    reasoning_effort: Mapped[str | None] = mapped_column(
        String(20)
    )  # Reasoning/thinking level: "none", "low", "medium", "high"
    model_config: Mapped[dict[str, Any] | None] = mapped_column(
        JSON
    )  # Additional model parameters (temperature, max_tokens, etc.)

    # Relationships
    documents: Mapped[list["DocumentResult"]] = relationship(
        "DocumentResult", back_populates="run", cascade="all, delete-orphan"
    )
    events: Mapped[list["RunEvent"]] = relationship("RunEvent", back_populates="run", cascade="all, delete-orphan")
    evaluation: Mapped["RunEvaluation | None"] = relationship(
        "RunEvaluation",
        back_populates="run",
        uselist=False,
        cascade="all, delete-orphan",
    )


class DocumentResult(Base):
    """Stores detailed evaluation results for individual test documents.

    Part of the EVALUATION SYSTEM - stores results from validator performance testing.

    Contains complete analysis including:
    - Document classification and validity determination
    - Stage-by-stage reasoning and validation checks
    - Ground truth comparison (expected vs predicted)
    - Correctness flags for accuracy measurement

    Production validation results (ValidationResult) are returned directly
    and not stored in this table - this is only for QA testing and evaluation.
    """

    __tablename__ = "document_results"
    __table_args__ = (
        # Composite indexes for common lookup patterns
        Index("ix_document_results_run_document", "run_id", "document_id"),
        # Additional indexes for query optimisation
        Index("ix_docs_run_validity", "run_id", "predicted_validity"),  # Filter by run and validity
        Index("ix_docs_run_correct", "run_id", "is_correct"),  # Correctness analysis queries
        # Check constraint for execution time
        CheckConstraint(
            "execution_time IS NULL OR execution_time >= 0",
            name="ck_document_results_execution_time_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("runs.id"), nullable=False, index=True)

    # Document identification
    document_id: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)

    # Review results (always present)
    # Use ValidityLabel enum: VALID, INVALID, CLARIFICATION_NEEDED, UNKNOWN, ERROR
    predicted_validity: Mapped[str] = mapped_column(String(50))
    predicted_reasoning: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[str | None] = mapped_column(String(50))  # HIGH, MEDIUM, LOW
    prompt_type: Mapped[str | None] = mapped_column(String(100))  # floor_plan, elevation, section, etc.
    execution_time: Mapped[float | None] = mapped_column(Float)

    # Ground truth comparison (only present if ground truth was provided)
    # Use ValidityLabel enum: VALID, INVALID, CLARIFICATION_NEEDED, UNKNOWN
    expected_validity: Mapped[str | None] = mapped_column(String(50))
    is_correct: Mapped[bool | None] = mapped_column()  # Whether prediction matched ground truth

    # Detailed results stored as JSON
    stages: Mapped[list[Any] | None] = mapped_column(JSON)  # Stage-by-stage processing details

    # Carbon impact metrics from LLM inference (nullable - not all evaluations track carbon)
    carbon_energy_kwh_min: Mapped[float | None] = mapped_column(Float)
    carbon_energy_kwh_max: Mapped[float | None] = mapped_column(Float)
    carbon_gwp_kgco2eq_min: Mapped[float | None] = mapped_column(Float)
    carbon_gwp_kgco2eq_max: Mapped[float | None] = mapped_column(Float)
    carbon_adpe_kgsbeq_min: Mapped[float | None] = mapped_column(Float)
    carbon_adpe_kgsbeq_max: Mapped[float | None] = mapped_column(Float)
    carbon_pe_mj_min: Mapped[float | None] = mapped_column(Float)
    carbon_pe_mj_max: Mapped[float | None] = mapped_column(Float)
    carbon_wcf_l_min: Mapped[float | None] = mapped_column(Float)
    carbon_wcf_l_max: Mapped[float | None] = mapped_column(Float)

    # Reasoning evaluation metrics (LLM-as-judge comparison of predicted vs expected reasoning)
    reasoning_match_score: Mapped[float | None] = mapped_column(Float)  # 0.0-1.0 semantic match score
    reasoning_evaluated: Mapped[bool] = mapped_column(default=False)  # Whether reasoning was evaluated
    reasoning_explanation: Mapped[str | None] = mapped_column(Text)  # Brief explanation of the match
    expected_reasoning: Mapped[str | None] = mapped_column(Text)  # Ground truth reasoning for reference

    # Relationship
    run: Mapped["Run"] = relationship("Run", back_populates="documents")


class RunEvaluation(Base):
    """Stores detailed evaluation statistics and metrics for QA test runs.

    Part of the EVALUATION SYSTEM - provides aggregate performance metrics
    for measuring validator quality over test datasets.

    This table only contains records for evaluation runs with ground truth data,
    providing aggregate statistics, confusion matrix metrics, and performance analysis:
    - Accuracy, precision, recall, F1 score
    - Confusion matrix (TP, TN, FP, FN)
    - Performance breakdown by document type
    - Confidence analysis
    - Error pattern analysis

    Production validation does not use this table - it's purely for QA testing.
    """

    __tablename__ = "run_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("runs.id"), nullable=False, unique=True, index=True)

    # Overall metrics
    overall_accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    precision: Mapped[float | None] = mapped_column(Float)
    recall: Mapped[float | None] = mapped_column(Float)
    f1_score: Mapped[float | None] = mapped_column(Float)

    # Confusion matrix counts
    true_positives: Mapped[int] = mapped_column(Integer, default=0)  # Correctly predicted VALID
    true_negatives: Mapped[int] = mapped_column(Integer, default=0)  # Correctly predicted INVALID
    false_positives: Mapped[int] = mapped_column(Integer, default=0)  # Predicted VALID, actually INVALID
    false_negatives: Mapped[int] = mapped_column(Integer, default=0)  # Predicted INVALID, actually VALID

    # Document type breakdown (stored as JSON for flexibility)
    accuracy_by_type: Mapped[dict[str, Any] | None] = mapped_column(
        JSON
    )  # e.g., {"floor_plan": 0.92, "elevation": 0.88}
    confusion_by_type: Mapped[dict[str, Any] | None] = mapped_column(JSON)  # Detailed breakdown by document type

    # Additional statistics
    avg_confidence_correct: Mapped[float | None] = mapped_column(Float)  # Average confidence for correct predictions
    avg_confidence_incorrect: Mapped[float | None] = mapped_column(
        Float
    )  # Average confidence for incorrect predictions
    avg_execution_time: Mapped[float | None] = mapped_column(Float)

    # Error analysis
    common_errors: Mapped[dict[str, Any] | None] = mapped_column(JSON)  # Most common error patterns
    error_rate_by_validity: Mapped[dict[str, Any] | None] = mapped_column(
        JSON
    )  # Error rates for VALID vs INVALID documents

    # Relationship
    run: Mapped["Run"] = relationship("Run", back_populates="evaluation")


class RunEvent(Base):
    """Stores detailed event log for run execution tracking.

    Events track the progression of runs including:
    - Stage completions (use Stage enum: CLASSIFICATION, VALIDATION)
    - Document processing events (use EventType enum)
    - Errors and warnings
    - Performance metrics
    """

    __tablename__ = "run_events"
    __table_args__ = (
        # Composite indexes for common query patterns
        Index("ix_run_events_run_timestamp", "run_id", "timestamp"),
        Index("ix_run_events_run_event_type", "run_id", "event_type", "timestamp"),
        Index("ix_run_events_document", "document_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("runs.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)

    # Event details
    # Use EventType enum: EVALUATION_STARTED, STAGE_COMPLETED, DOCUMENT_COMPLETED, etc.
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    document_id: Mapped[str | None] = mapped_column(String(500), index=True)
    data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    # Relationship
    run: Mapped["Run"] = relationship("Run", back_populates="events")


class PromptVersion(Base):
    """Stores prompt versions for tracking changes and A/B testing.

    Shared between PRODUCTION and EVALUATION systems - tracks prompt evolution.

    Enables prompt evolution tracking, A/B testing, and rollback capabilities:
    - Full prompt content and schema versioning
    - Usage statistics and performance metrics
    - Active version tracking
    - Rollback capability for prompt changes

    Used by both:
    - Production: For prompt deployment and rollback
    - Evaluation: For measuring prompt performance against test datasets

    Each version records the full prompt content and metadata about its usage.
    """

    __tablename__ = "prompt_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prompt_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )  # classification, floor_plan, elevation, etc.
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True
    )

    # Prompt content
    prompt_content: Mapped[str] = mapped_column(Text, nullable=False)
    schema_content: Mapped[str | None] = mapped_column(Text)  # For structured outputs

    # Metadata
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    created_by: Mapped[str | None] = mapped_column(String(200))

    # Usage statistics
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[float | None] = mapped_column(Float)
    avg_execution_time: Mapped[float | None] = mapped_column(Float)


class StoredFile(Base):
    """Stores file hash mappings for S3 object storage.

    Primarily used by EVALUATION SYSTEM for test dataset management.

    Maps original filenames to content hashes and S3 storage paths.
    This enables:
    - Content-addressable storage using SHA256 hashes
    - Deduplication (same content = same hash)
    - Safe handling of special characters in filenames
    - Tracking file metadata and associations with evaluation runs

    Production validation can use this for document storage, but validation
    itself is stateless - files are just inputs, not stored results.
    """

    __tablename__ = "stored_files"
    __table_args__ = (
        # Composite unique constraint: same file can be used in multiple runs
        UniqueConstraint("run_id", "content_hash", name="uq_run_content"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Content hash (SHA256) - NOT unique as same file can be in multiple runs
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Original filename from upload
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)

    # Storage path/key (e.g., "documents/hash.pdf") - same hash = same storage object
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False, index=True)

    # File metadata
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # Size in bytes
    mime_type: Mapped[str | None] = mapped_column(String(100))  # e.g., "application/pdf"

    # Association with run (optional - files can be uploaded before run starts)
    run_id: Mapped[str | None] = mapped_column(String(100), index=True)

    # File category (document, ground_truth, etc.)
    file_category: Mapped[str] = mapped_column(String(50), nullable=False, default="document", index=True)

    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True
    )
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Usage tracking
    access_count: Mapped[int] = mapped_column(Integer, default=0)
