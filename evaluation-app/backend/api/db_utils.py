from typing import Any, TypeVar

from sqlalchemy import Select, asc, desc
from sqlalchemy.orm import Session

from backend.api.error_handlers import bad_request, not_found
from backend.config import PaginationConfig

# Type variable for SQLAlchemy models
T = TypeVar("T")


def get_or_404(
    session: Session,
    model: type[T],
    filter_clause: Any,
    resource_name: str,
    identifier: str | None = None,
) -> T:
    """
    Retrieve a single record or raise 404 HTTPException.

    Executes a query for a single record and raises a standardised 404 error
    if the record is not found. Provides consistent error handling across all
    get-by-id endpoints.

    Args:
        session: SQLAlchemy database session
        model: SQLAlchemy model class to query
        filter_clause: SQLAlchemy filter condition (e.g., Model.id == value)
        resource_name: Human-readable resource name for error message (e.g., "Run", "Document")
        identifier: Optional identifier value to include in error message

    Returns:
        The found model instance

    Raises:
        HTTPException: 404 if record not found, with standardised error message

    Examples:
        >>> # Get run by run_id or 404
        >>> run = get_or_404(
        ...     session,
        ...     DBRun,
        ...     DBRun.run_id == "run_123",
        ...     "Run",
        ...     "run_123"
        ... )

        >>> # Get user by email or 404
        >>> user = get_or_404(
        ...     session,
        ...     User,
        ...     User.email == "user@example.com",
        ...     "User",
        ...     "user@example.com"
        ... )
    """
    record = session.query(model).filter(filter_clause).first()
    if not record:
        raise not_found(f"{resource_name} not found: {identifier}")
    return record


def validate_pagination(
    skip: int | None = None,
    limit: int | None = None,
    default_limit: int = PaginationConfig.DEFAULT_LIMIT,
    max_limit: int = PaginationConfig.MAX_LIMIT,
) -> tuple[int, int]:
    """
    Validate and normalise pagination parameters.

    Ensures skip and limit values are within acceptable ranges and returns
    normalised values with defaults applied. Raises appropriate validation
    errors for invalid inputs.

    Args:
        skip: Number of records to skip (offset). Must be non-negative. Defaults to 0.
        limit: Maximum number of records to return. Must not exceed max_limit. Defaults to default_limit.
        default_limit: Default limit if none provided (default: from PaginationConfig)
        max_limit: Maximum allowed limit (default: from PaginationConfig)

    Returns:
        Tuple of (skip, limit) with validated and normalised values

    Raises:
        HTTPException: 400 if skip is negative or limit exceeds maximum

    Examples:
        >>> # Use defaults
        >>> skip, limit = validate_pagination()
        >>> # Returns: (0, 100)

        >>> # Custom values
        >>> skip, limit = validate_pagination(skip=10, limit=50)
        >>> # Returns: (10, 50)

        >>> # Validation error - skip negative
        >>> skip, limit = validate_pagination(skip=-1)
        >>> # Raises: HTTPException(400, "Validation error for 'skip': Skip cannot be negative")

        >>> # Validation error - limit too high
        >>> skip, limit = validate_pagination(limit=2000)
        >>> # Raises: HTTPException(400, "Validation error for 'limit': Limit cannot exceed 1000")
    """
    # Normalise skip
    normalised_skip = skip if skip is not None else 0
    if normalised_skip < 0:
        raise bad_request("Validation error for 'skip': Skip cannot be negative")

    # Normalise limit
    normalised_limit = limit if limit is not None else default_limit
    if normalised_limit > max_limit:
        raise bad_request(f"Validation error for 'limit': Limit cannot exceed {max_limit}")

    return normalised_skip, normalised_limit


def get_list_with_pagination(
    session: Session,
    query: Select[tuple[T]],
    skip: int,
    limit: int,
    order_by: Any | None = None,
    order_desc: bool = True,
) -> list[T]:
    """
    Execute paginated query with standard ordering.

    Applies pagination parameters and optional ordering to a query, then
    executes and returns results. Provides consistent pagination behaviour
    across list endpoints.

    Args:
        session: SQLAlchemy database session
        query: SQLAlchemy select query to paginate
        skip: Number of records to skip (offset)
        limit: Maximum number of records to return
        order_by: Optional column to order by (default: no ordering)
        order_desc: Whether to order descending (default: True)

    Returns:
        List of model instances matching the query

    Examples:
        >>> # Get paginated runs ordered by timestamp descending
        >>> query = select(DBRun)
        >>> runs = get_list_with_pagination(
        ...     session,
        ...     query,
        ...     skip=0,
        ...     limit=100,
        ...     order_by=DBRun.timestamp,
        ...     order_desc=True
        ... )

        >>> # Get paginated users without ordering
        >>> query = select(User)
        >>> users = get_list_with_pagination(
        ...     session,
        ...     query,
        ...     skip=10,
        ...     limit=50
        ... )
    """
    # Apply ordering if specified
    if order_by is not None:
        if order_desc:
            query = query.order_by(desc(order_by))
        else:
            query = query.order_by(asc(order_by))

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute and return results
    return list(session.scalars(query).all())
