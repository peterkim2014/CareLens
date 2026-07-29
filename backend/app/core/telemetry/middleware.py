import logging
from time import perf_counter
from uuid import UUID, uuid4

from fastapi import Request
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.responses import Response

from app.core.telemetry.context import (
    reset_trace_id,
    set_trace_id,
)

TRACE_HEADER = "X-Trace-ID"

logger = logging.getLogger(__name__)


class TraceCorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        trace_id = self._resolve_trace_id(request.headers.get(TRACE_HEADER))

        token = set_trace_id(trace_id)
        started_at = perf_counter()

        try:
            response = await call_next(request)

            response.headers[TRACE_HEADER] = str(trace_id)

            duration_ms = round(
                (perf_counter() - started_at) * 1000,
                3,
            )

            logger.info(
                "HTTP request completed",
                extra={
                    "event": "http_request_completed",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

            return response
        except Exception as exception:
            duration_ms = round(
                (perf_counter() - started_at) * 1000,
                3,
            )

            logger.error(
                "HTTP request failed",
                extra={
                    "event": "http_request_failed",
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "error_type": type(exception).__name__,
                },
            )

            raise
        finally:
            reset_trace_id(token)

    @staticmethod
    def _resolve_trace_id(
        header_value: str | None,
    ) -> UUID:
        if header_value is None:
            return uuid4()

        try:
            return UUID(header_value)
        except ValueError:
            return uuid4()
