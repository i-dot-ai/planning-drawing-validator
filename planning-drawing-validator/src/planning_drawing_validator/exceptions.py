from typing import Any


class ReviewBaseException(Exception):
    """Base exception for all review application errors.

    All custom exceptions should inherit from this class to allow
    centralised exception handling and logging.

    Attributes:
        message: Human-readable error message
        details: Additional context about the error
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        """Initialise base exception.

        Args:
            message: Human-readable error description
            details: Optional dictionary with additional error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def __repr__(self) -> str:
        """Return detailed string representation."""
        if self.details:
            return f"{self.__class__.__name__}({self.message!r}, details={self.details!r})"
        return f"{self.__class__.__name__}({self.message!r})"


# Document-related exceptions
class DocumentError(ReviewBaseException):
    """Base class for document-related errors."""

    pass


class DocumentNotFoundError(DocumentError):
    """Raised when a requested document cannot be found.

    This typically indicates the document doesn't exist in storage
    or the provided identifier is invalid.
    """

    def __init__(self, document_id: str, details: dict[str, Any] | None = None):
        """Initialise DocumentNotFoundError.

        Args:
            document_id: The identifier of the missing document
            details: Additional context (e.g., storage location searched)
        """
        message = f"Document not found: {document_id}"
        super().__init__(message, details or {"document_id": document_id})


# LLM-related exceptions
class LLMError(ReviewBaseException):
    """Base class for LLM processing errors."""

    pass


# Configuration-related exceptions
class ConfigurationError(ReviewBaseException):
    """Base class for configuration errors.

    Raised when required configuration is missing or invalid.
    """

    pass
