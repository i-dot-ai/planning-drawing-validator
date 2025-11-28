from datetime import datetime
from typing import TypeAlias

# Domain Identifiers
RunID: TypeAlias = str
"""Unique identifier for an evaluation run (e.g., 'run_20251023_143022')."""

DocumentID: TypeAlias = str
"""Unique identifier for a document, typically filename without extension."""

VersionID: TypeAlias = str
"""Unique identifier for a prompt version (UUID format)."""

EventType: TypeAlias = str
"""Type of run event (e.g., 'stage_started', 'stage_completed')."""

# Storage and File System
StorageKey: TypeAlias = str
"""Storage object key/identifier (e.g., 'runs/run_123/documents/doc.pdf' for S3, Azure Blob path, etc.)."""

StoragePrefix: TypeAlias = str
"""Storage prefix for filtering/scoping objects (e.g., 'runs/run_123/' for S3, container prefix for Azure, etc.)."""

ContentHash: TypeAlias = str
"""SHA-256 hash of file content for deduplication (hex string)."""

Filename: TypeAlias = str
"""Original filename of uploaded or stored document."""

MimeType: TypeAlias = str
"""MIME type for document content (e.g., 'application/pdf', 'image/jpeg')."""

# Prompt Management
PromptName: TypeAlias = str
"""Name of a prompt template (e.g., 'classification_prompt', 'validation_prompt')."""

PromptType: TypeAlias = str
"""Type category of prompt (e.g., 'classification', 'validation')."""

# Validity and Status
ValidityStatus: TypeAlias = str
"""Document validity status ('VALID', 'INVALID', 'CLARIFICATION_NEEDED', 'UNKNOWN')."""

RunStatus: TypeAlias = str
"""Evaluation run status ('running', 'completed', 'failed', 'stopped')."""

# Temporal Types
Timestamp: TypeAlias = datetime
"""Datetime timestamp for events, runs, and versioning."""

# Metrics and Counts
Accuracy: TypeAlias = float
"""Accuracy metric as a decimal between 0.0 and 1.0."""

ExecutionTime: TypeAlias = float
"""Execution time in seconds."""

DocumentCount: TypeAlias = int
"""Count of documents in a collection or run."""
