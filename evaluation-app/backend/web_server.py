import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from planning_drawing_validator.config import get_config

from backend.api.routers import (
    documents_router,
    evaluation_router,
    ground_truth_router,
    health_router,
    models_router,
    prompts_router,
    runs_router,
    websocket_router,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan events (startup and shutdown)."""
    # Startup: Initialise prompt versions
    try:
        logger.info("Initialising prompt versions...")
        # Use the module-level prompt_manager instance
        from backend.api.dependencies import get_prompt_manager

        pm = get_prompt_manager()
        snapshots = pm.snapshot_all_prompts(author="system", description="Initial version (original prompt)")
        logger.info(f"Initialised {len(snapshots)} prompt versions")
    except Exception as e:
        logger.error(f"Failed to initialise prompt versions: {e}")

    yield  # Application runs here

    # Shutdown: cleanup if needed
    logger.info("Application shutting down...")


app = FastAPI(
    title="Drawing Validation Evaluation System",
    version="1.0.0",
    description=(
        "Drawing validationevaluation system for performance.\n\n"
        "This is the EVALUATION system (not production). It provides ground truth "
        "management, evaluation runs, performance metrics, and testing workflows "
        "for quality assurance.\n\n"
        "Production validation uses DocumentValidator and will have a separate "
        "user-facing API and frontend."
    ),
    lifespan=lifespan,
)

# CORS configuration - configurable via environment variable
_default_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
_cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
_cors_origins = (
    [o.strip() for o in _cors_origins_env.split(",") if o.strip()] if _cors_origins_env else _default_origins
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# Configuration
_, path_config = get_config()

app.include_router(health_router, tags=["health"])
app.include_router(documents_router, tags=["evaluation-documents"])
app.include_router(runs_router, tags=["evaluation-runs"])
app.include_router(evaluation_router, tags=["evaluation"])
app.include_router(ground_truth_router, tags=["evaluation-ground-truth"])
app.include_router(prompts_router, tags=["evaluation-prompts"])
app.include_router(models_router, tags=["models"])
app.include_router(websocket_router, tags=["websocket"])

# Serve React build files (evaluation frontend)
frontend_path = Path(__file__).parent / "frontend" / "build"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=frontend_path / "static"), name="static")

    @app.get("/")
    async def serve_frontend() -> FileResponse:
        return FileResponse(frontend_path / "index.html")
else:

    @app.get("/")
    async def frontend_not_built() -> dict[str, Any]:
        return {
            "message": "Frontend not built. Run 'cd review/frontend && npm run build' first.",
            "instructions": [
                "1. cd review/frontend",
                "2. npm install",
                "3. npm run build",
                "4. Restart the server",
            ],
        }


# Catch-all route for frontend client-side routing (must be last, after all API routes)
if frontend_path.exists():

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend_routes(full_path: str) -> FileResponse:
        # Don't serve frontend for API routes or websockets
        if full_path.startswith("api/") or full_path.startswith("ws/") or full_path == "ws":
            raise HTTPException(status_code=404, detail="Not found")

        # Serve index.html for all other paths (client-side routing)
        index_path = frontend_path / "index.html"
        if not index_path.exists():
            raise HTTPException(status_code=404, detail="Frontend not found")

        return FileResponse(index_path)


def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = True) -> None:
    """Run the evaluation system server."""
    uvicorn.run(
        "backend.web_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    run_server()
