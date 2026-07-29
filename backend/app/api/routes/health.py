from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    service: str
    version: str
    environment: str


@router.get(
    "",
    response_model=HealthResponse,
    summary="Check API health",
)
async def health_check() -> HealthResponse:
    settings = get_settings()

    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
