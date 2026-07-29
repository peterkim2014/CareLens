import logging
from time import perf_counter
from uuid import UUID, uuid4

from fastapi import Request
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.responses import Response
from starlette.routing import BaseRoute

from app.core.telemetry.context import (
    reset_trace_id,
    set_trace_id,
)
from app.core.telemetry.http_metrics import (
    HTTPMetrics,
)

TRACE_HEADER = "X-Trace-ID"

PROMETHEUS_METRICS_PATH = "/metrics"
UNMATCHED_ROUTE = "__unmatched__"

logger = logging.getLogger(__name__)


class TraceCorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        trace_id = self._resolve_trace_id(
            request.headers.get(
                TRACE_HEADER,
            )
        )

        token = set_trace_id(
            trace_id,
        )

        started_at = perf_counter()

        metrics: HTTPMetrics | None = getattr(
            request.app.state,
            "http_metrics",
            None,
        )

        should_record_metrics = (
            request.url.path
            != PROMETHEUS_METRICS_PATH
        )

        if (
            should_record_metrics
            and metrics is not None
        ):
            metrics.record_request_started()

        try:
            response = await call_next(
                request,
            )

            duration_seconds = (
                perf_counter() - started_at
            )

            route = self._resolve_route(
                request,
            )

            if (
                should_record_metrics
                and metrics is not None
            ):
                metrics.record_request_completed(
                    method=request.method,
                    route=route,
                    status_code=response.status_code,
                    duration_seconds=(
                        duration_seconds
                    ),
                )

            response.headers[TRACE_HEADER] = str(
                trace_id,
            )

            logger.info(
                "HTTP request completed",
                extra={
                    "event": "http_request_completed",
                    "method": request.method,
                    "route": route,
                    "status_code": (
                        response.status_code
                    ),
                    "duration_ms": round(
                        duration_seconds * 1000,
                        3,
                    ),
                },
            )

            return response
        except Exception as exception:
            duration_seconds = (
                perf_counter() - started_at
            )

            route = self._resolve_route(
                request,
            )

            if (
                should_record_metrics
                and metrics is not None
            ):
                metrics.record_request_completed(
                    method=request.method,
                    route=route,
                    status_code=500,
                    duration_seconds=(
                        duration_seconds
                    ),
                )

            logger.error(
                "HTTP request failed",
                extra={
                    "event": "http_request_failed",
                    "method": request.method,
                    "route": route,
                    "status_code": 500,
                    "duration_ms": round(
                        duration_seconds * 1000,
                        3,
                    ),
                    "error_type": type(
                        exception,
                    ).__name__,
                },
            )

            raise
        finally:
            reset_trace_id(
                token,
            )

    @staticmethod
    def _resolve_route(
        request: Request,
    ) -> str:
        route: BaseRoute | None = (
            request.scope.get(
                "route",
            )
        )

        route_path = getattr(
            route,
            "path",
            None,
        )

        if not isinstance(
            route_path,
            str,
        ):
            return UNMATCHED_ROUTE

        return route_path

    @staticmethod
    def _resolve_trace_id(
        header_value: str | None,
    ) -> UUID:
        if header_value is None:
            return uuid4()

        try:
            return UUID(
                header_value,
            )
        except ValueError:
            return uuid4()