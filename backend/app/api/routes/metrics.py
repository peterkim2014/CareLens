from fastapi import (
    APIRouter,
    Request,
)
from pydantic import BaseModel, Field

from app.core.metrics import (
    RetrievalMetrics,
    RetrievalMetricsSnapshot,
)

router = APIRouter(
    prefix="/metrics",
    tags=["Metrics"],
)


class RetrievalActivityMetrics(BaseModel):
    total_requests: int = Field(ge=0)
    semantic_attempts: int = Field(ge=0)
    semantic_successes: int = Field(ge=0)
    semantic_failures: int = Field(ge=0)
    lexical_fallbacks: int = Field(ge=0)
    semantic_success_rate: float = Field(
        ge=0.0,
        le=1.0,
    )


class RecoveryMetrics(BaseModel):
    attempts: int = Field(ge=0)
    successes: int = Field(ge=0)
    failures: int = Field(ge=0)
    success_rate: float = Field(
        ge=0.0,
        le=1.0,
    )


class IndexingMetrics(BaseModel):
    synchronizations: int = Field(ge=0)
    successes: int = Field(ge=0)
    failures: int = Field(ge=0)
    latest_duration_seconds: float | None = Field(
        default=None,
        ge=0.0,
    )
    average_duration_seconds: float = Field(
        ge=0.0,
    )
    total_duration_seconds: float = Field(
        ge=0.0,
    )


class RetrievalMetricsResponse(BaseModel):
    retrieval: RetrievalActivityMetrics
    recovery: RecoveryMetrics
    indexing: IndexingMetrics


@router.get(
    "/retrieval",
    response_model=RetrievalMetricsResponse,
    summary="Get retrieval metrics",
)
async def read_retrieval_metrics(
    request: Request,
) -> RetrievalMetricsResponse:
    metrics: RetrievalMetrics | None = getattr(
        request.app.state,
        "retrieval_metrics",
        None,
    )

    snapshot = (
        metrics.snapshot() if metrics is not None else RetrievalMetrics().snapshot()
    )

    return _build_metrics_response(
        snapshot,
    )


def _build_metrics_response(
    snapshot: RetrievalMetricsSnapshot,
) -> RetrievalMetricsResponse:
    return RetrievalMetricsResponse(
        retrieval=RetrievalActivityMetrics(
            total_requests=snapshot.total_requests,
            semantic_attempts=snapshot.semantic_attempts,
            semantic_successes=snapshot.semantic_successes,
            semantic_failures=snapshot.semantic_failures,
            lexical_fallbacks=snapshot.lexical_fallbacks,
            semantic_success_rate=_calculate_rate(
                numerator=snapshot.semantic_successes,
                denominator=snapshot.semantic_attempts,
            ),
        ),
        recovery=RecoveryMetrics(
            attempts=snapshot.recovery_attempts,
            successes=snapshot.recovery_successes,
            failures=snapshot.recovery_failures,
            success_rate=_calculate_rate(
                numerator=snapshot.recovery_successes,
                denominator=snapshot.recovery_attempts,
            ),
        ),
        indexing=IndexingMetrics(
            synchronizations=(snapshot.index_synchronizations),
            successes=(snapshot.index_synchronization_successes),
            failures=(snapshot.index_synchronization_failures),
            latest_duration_seconds=(snapshot.latest_indexing_duration_seconds),
            average_duration_seconds=_calculate_average(
                total=(snapshot.total_indexing_duration_seconds),
                count=snapshot.index_synchronizations,
            ),
            total_duration_seconds=(snapshot.total_indexing_duration_seconds),
        ),
    )


def _calculate_rate(
    *,
    numerator: int,
    denominator: int,
) -> float:
    if denominator <= 0:
        return 0.0

    return numerator / denominator


def _calculate_average(
    *,
    total: float,
    count: int,
) -> float:
    if count <= 0:
        return 0.0

    return total / count
