from backend.api.routers.documents import router as documents_router
from backend.api.routers.evaluation import router as evaluation_router
from backend.api.routers.ground_truth import router as ground_truth_router
from backend.api.routers.health import router as health_router
from backend.api.routers.models import router as models_router
from backend.api.routers.prompts import router as prompts_router
from backend.api.routers.runs import router as runs_router
from backend.api.routers.websocket import router as websocket_router

__all__ = [
    "health_router",
    "documents_router",
    "runs_router",
    "evaluation_router",
    "ground_truth_router",
    "prompts_router",
    "models_router",
    "websocket_router",
]
