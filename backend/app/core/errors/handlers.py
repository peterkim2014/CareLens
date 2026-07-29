import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.errors.exceptions import AnalysisPipelineError
from app.core.errors.schemas import (
    APIErrorCode,
    APIErrorDetail,
    APIErrorResponse,
)

logger = logging.getLogger(__name__)


async def handle_analysis_pipeline_error(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    del request

    if not isinstance(
        exception,
        AnalysisPipelineError,
    ):
        raise exception

    logger.error(
        "Analysis pipeline failed",
        extra={
            "event": "analysis_pipeline_failed",
            "failed_stage": exception.failed_stage,
            "retryable": exception.retryable,
            "audit_duration_ms": (exception.audit.total_duration_ms),
        },
    )

    response = APIErrorResponse(
        error=APIErrorDetail(
            code=APIErrorCode.ANALYSIS_PIPELINE_FAILED,
            message=("The analysis could not be completed safely. Please try again."),
            trace_id=exception.trace_id,
            failed_stage=exception.failed_stage,
            retryable=exception.retryable,
        )
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(mode="json"),
    )
