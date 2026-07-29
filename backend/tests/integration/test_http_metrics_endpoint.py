from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.core.telemetry import HTTPMetrics
from app.main import app

client = TestClient(
    app,
)


def test_successful_request_is_recorded(
    monkeypatch: MonkeyPatch,
) -> None:
    metrics = HTTPMetrics()

    monkeypatch.setattr(
        app.state,
        "http_metrics",
        metrics,
        raising=False,
    )

    response = client.get(
        "/api/v1/health",
    )

    assert response.status_code == 200

    snapshot = metrics.snapshot()

    assert len(snapshot.requests) == 1

    recorded_request = snapshot.requests[0]

    assert recorded_request.method == "GET"
    assert recorded_request.route == "/health"
    assert recorded_request.status_code == 200
    assert recorded_request.count == 1


def test_unknown_route_uses_controlled_label(
    monkeypatch: MonkeyPatch,
) -> None:
    metrics = HTTPMetrics()

    monkeypatch.setattr(
        app.state,
        "http_metrics",
        metrics,
        raising=False,
    )

    response = client.get(
        "/api/v1/patients/123456789"
    )

    assert response.status_code == 404

    snapshot = metrics.snapshot()

    assert len(snapshot.requests) == 1

    recorded_request = snapshot.requests[0]

    assert recorded_request.route == "__unmatched__"
    assert recorded_request.status_code == 404

    serialized_snapshot = repr(
        snapshot,
    )

    assert "123456789" not in serialized_snapshot
    assert "patients/123456789" not in serialized_snapshot


def test_prometheus_scrape_is_not_recorded(
    monkeypatch: MonkeyPatch,
) -> None:
    metrics = HTTPMetrics()

    monkeypatch.setattr(
        app.state,
        "http_metrics",
        metrics,
        raising=False,
    )

    first_response = client.get(
        "/metrics",
    )
    second_response = client.get(
        "/metrics",
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    snapshot = metrics.snapshot()

    assert snapshot.requests == ()
    assert snapshot.durations == ()
    assert snapshot.requests_in_progress == 0


def test_prometheus_exposes_http_metrics(
    monkeypatch: MonkeyPatch,
) -> None:
    metrics = HTTPMetrics()

    monkeypatch.setattr(
        app.state,
        "http_metrics",
        metrics,
        raising=False,
    )

    health_response = client.get(
        "/api/v1/health",
    )

    assert health_response.status_code == 200

    metrics_response = client.get(
        "/metrics",
    )

    assert metrics_response.status_code == 200

    body = metrics_response.text

    assert (
        "# TYPE carelens_http_requests_total counter"
        in body
    )

    assert (
        'carelens_http_requests_total{'
        'method="GET",'
        'route="/health",'
        'status_code="200"} 1'
        in body
    )

    assert (
        "carelens_http_request_duration_seconds_count"
        in body
    )

    assert (
        "carelens_http_request_duration_seconds_sum"
        in body
    )

    assert (
        "carelens_http_request_duration_seconds_average"
        in body
    )

    assert (
        "carelens_http_requests_in_progress 0"
        in body
    )


def test_prometheus_metrics_do_not_expose_query_strings(
    monkeypatch: MonkeyPatch,
) -> None:
    metrics = HTTPMetrics()

    monkeypatch.setattr(
        app.state,
        "http_metrics",
        metrics,
        raising=False,
    )

    response = client.get(
        "/api/v1/health",
        params={
            "patient_name": "Sensitive Person",
            "query": "private medical information",
        },
    )

    assert response.status_code == 200

    metrics_response = client.get(
        "/metrics",
    )

    body = metrics_response.text.lower()

    assert "sensitive person" not in body
    assert "private medical information" not in body
    assert "patient_name" not in body
    assert "query=" not in body