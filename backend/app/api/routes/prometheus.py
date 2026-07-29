from fastapi import (
    APIRouter,
    Request,
    Response,
)

from app.core.metrics import (
    RetrievalMetrics,
    RetrievalMetricsSnapshot,
)
from app.core.telemetry import (
    HTTPMetrics,
    HTTPMetricsSnapshot,
)

router = APIRouter()

PROMETHEUS_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"


@router.get(
    "/metrics",
    include_in_schema=False,
    response_class=Response,
)
async def read_prometheus_metrics(
    request: Request,
) -> Response:
    retrieval_metrics: RetrievalMetrics | None = getattr(
        request.app.state,
        "retrieval_metrics",
        None,
    )

    http_metrics: HTTPMetrics | None = getattr(
        request.app.state,
        "http_metrics",
        None,
    )

    retrieval_snapshot = (
        retrieval_metrics.snapshot()
        if retrieval_metrics is not None
        else RetrievalMetrics().snapshot()
    )

    http_snapshot = (
        http_metrics.snapshot()
        if http_metrics is not None
        else HTTPMetrics().snapshot()
    )

    content = _build_prometheus_response(
        retrieval_snapshot,
        http_snapshot=http_snapshot,
    )

    return Response(
        content=content,
        media_type=PROMETHEUS_CONTENT_TYPE,
    )


def _build_prometheus_response(
    snapshot: RetrievalMetricsSnapshot,
    *,
    http_snapshot: HTTPMetricsSnapshot | None = None,
) -> str:
    semantic_success_ratio = _calculate_ratio(
        numerator=snapshot.semantic_successes,
        denominator=snapshot.semantic_attempts,
    )

    recovery_success_ratio = _calculate_ratio(
        numerator=snapshot.recovery_successes,
        denominator=snapshot.recovery_attempts,
    )

    average_indexing_duration = _calculate_average(
        total=snapshot.total_indexing_duration_seconds,
        count=snapshot.index_synchronizations,
    )

    latest_indexing_duration = (
        snapshot.latest_indexing_duration_seconds
        if snapshot.latest_indexing_duration_seconds is not None
        else 0.0
    )

    lines = [
        "# HELP carelens_retrieval_requests_total Total retrieval requests.",
        "# TYPE carelens_retrieval_requests_total counter",
        _metric_line(
            "carelens_retrieval_requests_total",
            snapshot.total_requests,
        ),
        "# HELP carelens_semantic_attempts_total Total semantic retrieval attempts.",
        "# TYPE carelens_semantic_attempts_total counter",
        _metric_line(
            "carelens_semantic_attempts_total",
            snapshot.semantic_attempts,
        ),
        "# HELP carelens_semantic_successes_total "
        "Total successful semantic retrieval attempts.",
        "# TYPE carelens_semantic_successes_total counter",
        _metric_line(
            "carelens_semantic_successes_total",
            snapshot.semantic_successes,
        ),
        "# HELP carelens_semantic_failures_total "
        "Total failed semantic retrieval attempts.",
        "# TYPE carelens_semantic_failures_total counter",
        _metric_line(
            "carelens_semantic_failures_total",
            snapshot.semantic_failures,
        ),
        "# HELP carelens_lexical_fallbacks_total "
        "Total lexical fallbacks after semantic failure.",
        "# TYPE carelens_lexical_fallbacks_total counter",
        _metric_line(
            "carelens_lexical_fallbacks_total",
            snapshot.lexical_fallbacks,
        ),
        "# HELP carelens_semantic_success_ratio "
        "Ratio of successful semantic retrieval attempts.",
        "# TYPE carelens_semantic_success_ratio gauge",
        _metric_line(
            "carelens_semantic_success_ratio",
            semantic_success_ratio,
        ),
        "# HELP carelens_recovery_attempts_total "
        "Total semantic runtime recovery attempts.",
        "# TYPE carelens_recovery_attempts_total counter",
        _metric_line(
            "carelens_recovery_attempts_total",
            snapshot.recovery_attempts,
        ),
        "# HELP carelens_recovery_successes_total "
        "Total successful semantic runtime recoveries.",
        "# TYPE carelens_recovery_successes_total counter",
        _metric_line(
            "carelens_recovery_successes_total",
            snapshot.recovery_successes,
        ),
        "# HELP carelens_recovery_failures_total "
        "Total failed semantic runtime recoveries.",
        "# TYPE carelens_recovery_failures_total counter",
        _metric_line(
            "carelens_recovery_failures_total",
            snapshot.recovery_failures,
        ),
        "# HELP carelens_recovery_success_ratio "
        "Ratio of successful semantic runtime recoveries.",
        "# TYPE carelens_recovery_success_ratio gauge",
        _metric_line(
            "carelens_recovery_success_ratio",
            recovery_success_ratio,
        ),
        "# HELP carelens_index_synchronizations_total "
        "Total semantic index synchronizations.",
        "# TYPE carelens_index_synchronizations_total counter",
        _metric_line(
            "carelens_index_synchronizations_total",
            snapshot.index_synchronizations,
        ),
        "# HELP "
        "carelens_index_synchronization_successes_total "
        "Total successful semantic index synchronizations.",
        "# TYPE carelens_index_synchronization_successes_total counter",
        _metric_line(
            "carelens_index_synchronization_successes_total",
            snapshot.index_synchronization_successes,
        ),
        "# HELP "
        "carelens_index_synchronization_failures_total "
        "Total failed semantic index synchronizations.",
        "# TYPE carelens_index_synchronization_failures_total counter",
        _metric_line(
            "carelens_index_synchronization_failures_total",
            snapshot.index_synchronization_failures,
        ),
        "# HELP carelens_indexing_latest_duration_seconds "
        "Duration of the latest semantic index "
        "synchronization.",
        "# TYPE carelens_indexing_latest_duration_seconds gauge",
        _metric_line(
            "carelens_indexing_latest_duration_seconds",
            latest_indexing_duration,
        ),
        "# HELP carelens_indexing_average_duration_seconds "
        "Average semantic index synchronization duration.",
        "# TYPE carelens_indexing_average_duration_seconds gauge",
        _metric_line(
            "carelens_indexing_average_duration_seconds",
            average_indexing_duration,
        ),
        "# HELP carelens_indexing_duration_seconds_total "
        "Total time spent synchronizing the semantic index.",
        "# TYPE carelens_indexing_duration_seconds_total counter",
        _metric_line(
            "carelens_indexing_duration_seconds_total",
            snapshot.total_indexing_duration_seconds,
        ),
    ]

    if http_snapshot is not None:
        lines.extend(
            _build_http_metrics_lines(
                http_snapshot,
            )
        )

    return "\n".join(lines) + "\n"


def _build_http_metrics_lines(
    snapshot: HTTPMetricsSnapshot,
) -> list[str]:
    lines = [
        "# HELP carelens_http_requests_total Total completed HTTP requests.",
        "# TYPE carelens_http_requests_total counter",
    ]

    for request_metric in snapshot.requests:
        lines.append(
            _labeled_metric_line(
                "carelens_http_requests_total",
                labels={
                    "method": request_metric.method,
                    "route": request_metric.route,
                    "status_code": str(request_metric.status_code),
                },
                value=request_metric.count,
            )
        )

    lines.extend(
        [
            "# HELP "
            "carelens_http_request_duration_seconds_count "
            "Number of measured HTTP request durations.",
            "# TYPE carelens_http_request_duration_seconds_count counter",
        ]
    )

    for duration_metric in snapshot.durations:
        labels = {
            "method": duration_metric.method,
            "route": duration_metric.route,
        }

        lines.append(
            _labeled_metric_line(
                "carelens_http_request_duration_seconds_count",
                labels=labels,
                value=duration_metric.count,
            )
        )

    lines.extend(
        [
            "# HELP "
            "carelens_http_request_duration_seconds_sum "
            "Total HTTP request duration in seconds.",
            "# TYPE carelens_http_request_duration_seconds_sum counter",
        ]
    )

    for duration_metric in snapshot.durations:
        labels = {
            "method": duration_metric.method,
            "route": duration_metric.route,
        }

        lines.append(
            _labeled_metric_line(
                "carelens_http_request_duration_seconds_sum",
                labels=labels,
                value=(duration_metric.total_duration_seconds),
            )
        )

    lines.extend(
        [
            "# HELP "
            "carelens_http_request_duration_seconds_average "
            "Average HTTP request duration in seconds.",
            "# TYPE carelens_http_request_duration_seconds_average gauge",
        ]
    )

    for duration_metric in snapshot.durations:
        average_duration = _calculate_average(
            total=(duration_metric.total_duration_seconds),
            count=duration_metric.count,
        )

        lines.append(
            _labeled_metric_line(
                "carelens_http_request_duration_seconds_average",
                labels={
                    "method": duration_metric.method,
                    "route": duration_metric.route,
                },
                value=average_duration,
            )
        )

    lines.extend(
        [
            "# HELP carelens_http_requests_in_progress "
            "Current number of HTTP requests in progress.",
            "# TYPE carelens_http_requests_in_progress gauge",
            _metric_line(
                "carelens_http_requests_in_progress",
                snapshot.requests_in_progress,
            ),
        ]
    )

    return lines


def _labeled_metric_line(
    name: str,
    *,
    labels: dict[str, str],
    value: int | float,
) -> str:
    serialized_labels = ",".join(
        f'{key}="{_escape_label_value(label_value)}"'
        for key, label_value in sorted(
            labels.items(),
        )
    )

    return f"{name}{{{serialized_labels}}} {_format_metric_value(value)}"


def _escape_label_value(
    value: str,
) -> str:
    return (
        value.replace(
            "\\",
            "\\\\",
        )
        .replace(
            "\n",
            "\\n",
        )
        .replace(
            '"',
            '\\"',
        )
    )


def _metric_line(
    name: str,
    value: int | float,
) -> str:
    return f"{name} {_format_metric_value(value)}"


def _format_metric_value(
    value: int | float,
) -> str:
    if isinstance(
        value,
        int,
    ):
        return str(value)

    return format(
        value,
        ".15g",
    )


def _calculate_ratio(
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
