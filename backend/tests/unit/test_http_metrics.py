import pytest

from app.core.telemetry import HTTPMetrics


def test_http_metrics_starts_empty() -> None:
    metrics = HTTPMetrics()

    snapshot = metrics.snapshot()

    assert snapshot.requests == ()
    assert snapshot.durations == ()
    assert snapshot.requests_in_progress == 0


def test_http_metrics_records_request_completion() -> None:
    metrics = HTTPMetrics()

    metrics.record_request_started()

    metrics.record_request_completed(
        method="get",
        route="/api/v1/health",
        status_code=200,
        duration_seconds=0.25,
    )

    snapshot = metrics.snapshot()

    assert snapshot.requests_in_progress == 0
    assert len(snapshot.requests) == 1
    assert len(snapshot.durations) == 1

    request = snapshot.requests[0]

    assert request.method == "GET"
    assert request.route == "/api/v1/health"
    assert request.status_code == 200
    assert request.count == 1

    duration = snapshot.durations[0]

    assert duration.method == "GET"
    assert duration.route == "/api/v1/health"
    assert duration.count == 1
    assert (
        duration.total_duration_seconds
        == pytest.approx(0.25)
    )


def test_http_metrics_aggregates_repeated_requests() -> None:
    metrics = HTTPMetrics()

    for duration in (
        0.1,
        0.2,
        0.3,
    ):
        metrics.record_request_started()

        metrics.record_request_completed(
            method="POST",
            route="/api/v1/analysis",
            status_code=200,
            duration_seconds=duration,
        )

    snapshot = metrics.snapshot()

    assert snapshot.requests[0].count == 3
    assert snapshot.durations[0].count == 3
    assert (
        snapshot.durations[
            0
        ].total_duration_seconds
        == pytest.approx(0.6)
    )


def test_http_metrics_separates_status_codes() -> None:
    metrics = HTTPMetrics()

    for status_code in (
        200,
        422,
        500,
    ):
        metrics.record_request_started()

        metrics.record_request_completed(
            method="POST",
            route="/api/v1/analysis",
            status_code=status_code,
            duration_seconds=0.1,
        )

    snapshot = metrics.snapshot()

    assert len(snapshot.requests) == 3
    assert snapshot.durations[0].count == 3


def test_http_metrics_normalizes_negative_duration() -> None:
    metrics = HTTPMetrics()

    metrics.record_request_started()

    metrics.record_request_completed(
        method="GET",
        route="/api/v1/health",
        status_code=200,
        duration_seconds=-1.0,
    )

    snapshot = metrics.snapshot()

    assert (
        snapshot.durations[
            0
        ].total_duration_seconds
        == 0.0
    )


def test_http_metrics_never_has_negative_in_progress_count() -> None:
    metrics = HTTPMetrics()

    metrics.record_request_completed(
        method="GET",
        route="/api/v1/health",
        status_code=200,
        duration_seconds=0.1,
    )

    assert (
        metrics.snapshot().requests_in_progress
        == 0
    )