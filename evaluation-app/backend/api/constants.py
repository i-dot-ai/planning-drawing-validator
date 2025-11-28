from enum import Enum


class Stage(str, Enum):
    """Evaluation pipeline stages."""

    CLASSIFICATION = "classification"
    VALIDATION = "validation"


class EventType(str, Enum):
    """WebSocket event types for real-time updates."""

    # Evaluation lifecycle events
    EVALUATION_STARTED = "evaluation_started"
    EVALUATION_COMPLETED = "evaluation_completed"
    EVALUATION_STOPPED = "evaluation_stopped"

    # Document processing events
    DOCUMENT_STARTED = "document_started"
    DOCUMENT_COMPLETED = "document_completed"
    DOCUMENT_ERROR = "document_error"

    # Stage events
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"

    # Queue status events
    QUEUE_STATUS = "queue_status"


class RunStatus(str, Enum):
    """Evaluation run status values."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class ValidityLabel(str, Enum):
    """Document validity classification labels."""

    VALID = "VALID"
    INVALID = "INVALID"
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"
