from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.core.metrics import RetrievalMetrics
from app.main import app

client = TestClient(
    app,
)


def test_prometheus_metrics_returns_zero_values_when_missing(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.delattr(
        app.state,
        "retrieval_metrics",
        raising=False,
    )

    response = client.get(
        "/metrics",
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/plain",
    )

    body = response.text

    assert "carelens_retrieval_requests_total 0" in body
    assert "carelens_semantic_attempts_total 0" in body
    assert "carelens_semantic_success_ratio 0" in body
    assert "carelens_recovery_success_ratio 0" in body
    assert "carelens_indexing_latest_duration_seconds 0" in body
    assert "carelens_indexing_average_duration_seconds 0" in body


def test_prometheus_metrics_returns_current_snapshot(
    monkeypatch: MonkeyPatch,
) -> None:
    metrics = RetrievalMetrics()

    for _ in range(
        4,
    ):
        metrics.record_request()

    for _ in range(
        3,
    ):
        metrics.record_semantic_attempt()

    metrics.record_semantic_success()
    metrics.record_semantic_success()
    metrics.record_semantic_failure()
    metrics.record_lexical_fallback()

    metrics.record_recovery_attempt()
    metrics.record_recovery_attempt()
    metrics.record_recovery_success()
    metrics.record_recovery_failure()

    metrics.record_index_synchronization(
        duration_seconds=0.2,
        succeeded=True,
    )
    metrics.record_index_synchronization(
        duration_seconds=0.4,
        succeeded=False,
    )

    monkeypatch.setattr(
        app.state,
        "retrieval_metrics",
        metrics,
        raising=False,
    )

    response = client.get(
        "/metrics",
    )

    assert response.status_code == 200

    body = response.text

    assert "carelens_retrieval_requests_total 4" in body
    assert "carelens_semantic_attempts_total 3" in body
    assert "carelens_semantic_successes_total 2" in body
    assert "carelens_semantic_failures_total 1" in body
    assert "carelens_lexical_fallbacks_total 1" in body
    assert "carelens_semantic_success_ratio 0.666666666666667" in body

    assert "carelens_recovery_attempts_total 2" in body
    assert "carelens_recovery_successes_total 1" in body
    assert "carelens_recovery_failures_total 1" in body
    assert "carelens_recovery_success_ratio 0.5" in body

    assert "carelens_index_synchronizations_total 2" in body
    assert "carelens_index_synchronization_successes_total 1" in body
    assert "carelens_index_synchronization_failures_total 1" in body
    assert "carelens_indexing_latest_duration_seconds 0.4" in body
    assert "carelens_indexing_average_duration_seconds 0.3" in body
    assert "carelens_indexing_duration_seconds_total 0.6" in body


def test_prometheus_metrics_includes_help_and_type_metadata(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        app.state,
        "retrieval_metrics",
        RetrievalMetrics(),
        raising=False,
    )

    response = client.get(
        "/metrics",
    )

    assert response.status_code == 200

    body = response.text

    assert "# HELP carelens_retrieval_requests_total" in body
    assert "# TYPE carelens_retrieval_requests_total counter" in body
    assert "# HELP carelens_semantic_success_ratio" in body
    assert "# TYPE carelens_semantic_success_ratio gauge" in body
    assert "# TYPE carelens_indexing_duration_seconds_total counter" in body


def test_prometheus_metrics_uses_root_route() -> None:
    response = client.get(
        "/api/v1/metrics",
    )

    assert response.status_code == 404


def test_prometheus_metrics_does_not_expose_sensitive_data(
    monkeypatch: MonkeyPatch,
) -> None:
    metrics = RetrievalMetrics()

    metrics.record_request()
    metrics.record_semantic_attempt()
    metrics.record_semantic_failure()
    metrics.record_lexical_fallback()

    monkeypatch.setattr(
        app.state,
        "retrieval_metrics",
        metrics,
        raising=False,
    )

    response = client.get(
        "/metrics",
    )

    assert response.status_code == 200

    body = response.text.lower()

    assert "query_text" not in body
    assert "exception_message" not in body
    assert "patient_name" not in body
    assert "provider unavailable" not in body
    assert "query_text" not in body
    assert "exception_message" not in body
    assert "patient_name" not in body
    assert "provider unavailable" not in body
    assert "__traceback__" not in body


def test_prometheus_metrics_ends_with_newline(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        app.state,
        "retrieval_metrics",
        RetrievalMetrics(),
        raising=False,
    )

    response = client.get(
        "/metrics",
    )

    assert response.status_code == 200
    assert response.text.endswith(
        "\n",
    )
