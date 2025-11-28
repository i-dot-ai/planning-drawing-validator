from fastapi import APIRouter

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        dict: Status information indicating the service is healthy.
    """
    return {
        "status": "healthy",
        "service": "evaluation-system",
        "version": "1.0.0",
    }
