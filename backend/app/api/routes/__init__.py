from fastapi import APIRouter

from app.api.routes.analysis import (
    router as analysis_router,
)
from app.api.routes.health import (
    router as health_router,
)
from app.api.routes.metrics import (
    router as metrics_router,
)

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(metrics_router)
api_router.include_router(analysis_router)

__all__ = ["api_router"]
