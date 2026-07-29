import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.core.metrics import RetrievalMetrics
from app.main import app

client = TestClient(
    app,
)


def test_retrieval_metrics_returns_zero_values_when_missing(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.delattr(
        app.state,
        "retrieval_metrics",
        raising=False,
    )

    response = client.get(
        "/api/v1/metrics/retrieval",
    )

    assert response.status_code == 200
    assert response.json() == {
        "retrieval": {
            "total_requests": 0,
            "semantic_attempts": 0,
            "semantic_successes": 0,
            "semantic_failures": 0,
            "lexical_fallbacks": 0,
            "semantic_success_rate": 0.0,
        },
        "recovery": {
            "attempts": 0,
            "successes": 0,
            "failures": 0,
            "success_rate": 0.0,
        },
        "indexing": {
            "synchronizations": 0,
            "successes": 0,
            "failures": 0,
            "latest_duration_seconds": None,
            "average_duration_seconds": 0.0,
            "total_duration_seconds": 0.0,
        },
    }


def test_retrieval_metrics_returns_current_snapshot(
    monkeypatch: MonkeyPatch,
) -> None:
    metrics = RetrievalMetrics()

    metrics.record_request()
    metrics.record_request()
    metrics.record_request()
    metrics.record_request()

    metrics.record_semantic_attempt()
    metrics.record_semantic_attempt()
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
        "/api/v1/metrics/retrieval",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["retrieval"] == {
        "total_requests": 4,
        "semantic_attempts": 3,
        "semantic_successes": 2,
        "semantic_failures": 1,
        "lexical_fallbacks": 1,
        "semantic_success_rate": (2 / 3),
    }

    assert body["recovery"] == {
        "attempts": 2,
        "successes": 1,
        "failures": 1,
        "success_rate": 0.5,
    }

    indexing = body["indexing"]

    assert indexing["synchronizations"] == 2
    assert indexing["successes"] == 1
    assert indexing["failures"] == 1
    assert indexing["latest_duration_seconds"] == pytest.approx(
        0.4,
    )
    assert indexing["average_duration_seconds"] == pytest.approx(
        0.3,
    )
    assert indexing["total_duration_seconds"] == pytest.approx(
        0.6,
    )


def test_retrieval_metrics_protects_against_zero_division(
    monkeypatch: MonkeyPatch,
) -> None:
    metrics = RetrievalMetrics()

    monkeypatch.setattr(
        app.state,
        "retrieval_metrics",
        metrics,
        raising=False,
    )

    response = client.get(
        "/api/v1/metrics/retrieval",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["retrieval"]["semantic_success_rate"] == 0.0
    assert body["recovery"]["success_rate"] == 0.0
    assert body["indexing"]["average_duration_seconds"] == 0.0


def test_retrieval_metrics_does_not_expose_sensitive_data(
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
        "/api/v1/metrics/retrieval",
    )

    assert response.status_code == 200

    serialized_body = response.text.lower()

    assert "query" not in serialized_body
    assert "error" not in serialized_body
    assert "exception" not in serialized_body
    assert "patient" not in serialized_body
    assert "provider unavailable" not in serialized_body


def test_unknown_metrics_route_returns_not_found() -> None:
    response = client.get(
        "/api/v1/metrics/does-not-exist",
    )

    assert response.status_code == 404
