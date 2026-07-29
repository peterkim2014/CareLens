from typing import Literal

from fastapi import (
    APIRouter,
    Request,
)
from pydantic import BaseModel

from app.ai.retrieval.semantic.runtime import (
    SemanticRuntime,
)
from app.core.config import get_settings

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)

SemanticRetrievalStatus = Literal[
    "disabled",
    "available",
    "unavailable",
]


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    service: str
    version: str
    environment: str
    semantic_retrieval_enabled: bool
    semantic_retrieval_status: SemanticRetrievalStatus


@router.get(
    "",
    response_model=HealthResponse,
    summary="Check API health",
)
async def health_check(
    request: Request,
) -> HealthResponse:
    settings = get_settings()

    semantic_runtime: SemanticRuntime | None = getattr(
        request.app.state,
        "semantic_runtime",
        None,
    )

    semantic_status = _get_semantic_retrieval_status(
        enabled=(settings.semantic_retrieval_enabled),
        runtime=semantic_runtime,
    )

    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        semantic_retrieval_enabled=(settings.semantic_retrieval_enabled),
        semantic_retrieval_status=(semantic_status),
    )


def _get_semantic_retrieval_status(
    *,
    enabled: bool,
    runtime: SemanticRuntime | None,
) -> SemanticRetrievalStatus:
    if not enabled:
        return "disabled"

    if runtime is None:
        return "unavailable"

    if runtime.is_available:
        return "available"

    return "unavailable"
