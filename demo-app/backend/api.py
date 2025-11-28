"""FastAPI application for planning drawing validation.

Simple, stateless demo API for validating planning drawings against UK requirements.
"""

import logging
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from planning_drawing_validator.models import Document
from planning_drawing_validator.pipeline.schemas import DocumentType
from planning_drawing_validator.validator import DocumentValidator

from backend.schemas import HealthResponse, ValidationResponse
from backend.transformers import transform_validation_result
from backend.utils import get_drawing_type_info

logger = logging.getLogger(__name__)


# ============================================================================
# Application Lifespan
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events."""
    logger.info("Demo backend starting...")

    # Create upload directory
    app.state.upload_dir = Path("/app/data/uploads")
    app.state.upload_dir.mkdir(parents=True, exist_ok=True)

    # Initialise validator
    app.state.validator = DocumentValidator()

    yield

    logger.info("Demo backend shutting down...")


# ============================================================================
# Application Setup
# ============================================================================


app = FastAPI(
    title="Planning Drawing Validation API",
    version="1.0.0",
    description="Validate planning drawings against UK planning requirements using AI.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns service status and version information.
    """
    return HealthResponse(
        status="healthy",
        service="demo-validation-api",
        version="1.0.0",
    )


@app.get("/drawing-types", tags=["validation"])
async def get_drawing_types() -> dict[str, list[dict[str, Any]]]:
    """Get all supported drawing types and their validation requirements.

    Dynamically extracts information from Pydantic validation models.
    """
    drawing_types = [
        get_drawing_type_info(doc_type)
        for doc_type in DocumentType
        if doc_type not in [DocumentType.MIXED_PLANS, DocumentType.OTHER_PLANS]
    ]

    # Filter out types without requirements
    return {"drawing_types": [dt for dt in drawing_types if dt["requirements"]]}


@app.post("/validate", response_model=ValidationResponse, tags=["validation"])
async def validate_document(file: UploadFile = File(...)) -> ValidationResponse:
    """Validate a planning document against UK planning requirements.

    Accepts PDF, PNG, JPG, and other image formats. Returns detailed validation
    results including document classification, requirement checks, and reasoning.

    Args:
        file: Uploaded document file

    Returns:
        Validation result with document type, validity, and detailed checks

    Raises:
        HTTPException: If validation fails or file cannot be processed
    """
    temp_file_path = None

    try:
        # Generate unique document ID
        document_id = str(uuid.uuid4())

        # Save uploaded file temporarily
        filename = file.filename or f"upload_{document_id}"
        temp_file_path = app.state.upload_dir / filename

        content = await file.read()
        temp_file_path.write_bytes(content)

        # Create document object
        document = Document(
            document_id=document_id,
            filename=filename,
            file_path=str(temp_file_path),
            storage_key=None,
        )

        # Validate document with humanised reasoning for user-friendly display
        result = await app.state.validator.validate(document, humanise_reasoning=True)

        # Check for validation errors
        if not result.success:
            error_detail = result.error_message or "Unknown validation error occurred"
            raise HTTPException(status_code=500, detail=f"Validation failed: {error_detail}")

        # Transform result to API response format
        return transform_validation_result(document_id, result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")


# ============================================================================
# Server Entry Point
# ============================================================================


def run_server(host: str = "127.0.0.1", port: int = 8001, reload: bool = True) -> None:
    """Run the demo backend server.

    Args:
        host: Host address to bind to
        port: Port number (default 8001 to avoid conflict with evaluation app)
        reload: Enable auto-reload on code changes
    """
    uvicorn.run(
        "backend.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    run_server()
