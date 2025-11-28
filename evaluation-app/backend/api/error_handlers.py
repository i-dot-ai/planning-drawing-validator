from typing import Any

from fastapi import HTTPException


def bad_request(message: str) -> HTTPException:
    """Create a 400 Bad Request HTTP exception.

    Args:
        message: Error message to return to the client.

    Returns:
        HTTPException with status code 400.
    """
    return HTTPException(status_code=400, detail=message)


def not_found(message: str) -> HTTPException:
    """Create a 404 Not Found HTTP exception.

    Args:
        message: Error message to return to the client.

    Returns:
        HTTPException with status code 404.
    """
    return HTTPException(status_code=404, detail=message)


def internal_error(message: str) -> HTTPException:
    """Create a 500 Internal Server Error HTTP exception.

    Args:
        message: Error message to return to the client.

    Returns:
        HTTPException with status code 500.
    """
    return HTTPException(status_code=500, detail=message)


def conflict(message: str) -> HTTPException:
    """Create a 409 Conflict HTTP exception.

    Args:
        message: Error message to return to the client.

    Returns:
        HTTPException with status code 409.
    """
    return HTTPException(status_code=409, detail=message)


def handle_error(e: Exception, context: dict[str, Any] | None = None) -> HTTPException:
    """Convert a generic exception to an HTTP exception.

    Args:
        e: Exception to convert.
        context: Optional context dictionary (currently ignored).

    Returns:
        HTTPException with status code 500 and the exception message.
    """
    return HTTPException(status_code=500, detail=str(e))
