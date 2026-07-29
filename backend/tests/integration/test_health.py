from datetime import (
    UTC,
    datetime,
)
from types import SimpleNamespace
from typing import cast

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.ai.retrieval.semantic.runtime import (
    SemanticRuntime,
)
from app.api.routes import health
from app.core.config import Settings
from app.main import app

client = TestClient(app)


def create_semantic_runtime_state(
    *,
    is_available: bool,
    should_attempt_recovery: bool,
    startup_error: str | None = None,
    last_failure_at: datetime | None = None,
    last_recovery_attempt_at: datetime | None = None,
) -> SemanticRuntime:
    return cast(
        SemanticRuntime,
        SimpleNamespace(
            is_available=is_available,
            startup_error=startup_error,
            last_failure_at=last_failure_at,
            last_recovery_attempt_at=(last_recovery_attempt_at),
            should_attempt_recovery=(lambda: should_attempt_recovery),
        ),
    )


def test_health_check_returns_disabled_semantic_status(
    monkeypatch: MonkeyPatch,
) -> None:
    settings = Settings(
        environment="test",
        semantic_retrieval_enabled=False,
        semantic_recovery_cooldown_seconds=60.0,
    )

    monkeypatch.setattr(
        health,
        "get_settings",
        lambda: settings,
    )

    monkeypatch.setattr(
        app.state,
        "semantic_runtime",
        None,
        raising=False,
    )

    response = client.get(
        "/api/v1/health",
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "CareLens API",
        "version": "0.1.0",
        "environment": "test",
        "semantic_retrieval_enabled": False,
        "semantic_retrieval_status": "disabled",
        "semantic_retrieval_error": None,
        "semantic_last_failure_at": None,
        "semantic_last_recovery_attempt_at": None,
        "semantic_recovery_cooldown_seconds": 60.0,
    }


def test_health_check_returns_available_semantic_status(
    monkeypatch: MonkeyPatch,
) -> None:
    settings = Settings(
        environment="test",
        semantic_retrieval_enabled=True,
        semantic_recovery_cooldown_seconds=60.0,
    )

    runtime = create_semantic_runtime_state(
        is_available=True,
        should_attempt_recovery=False,
    )

    monkeypatch.setattr(
        health,
        "get_settings",
        lambda: settings,
    )

    monkeypatch.setattr(
        app.state,
        "semantic_runtime",
        runtime,
        raising=False,
    )

    response = client.get(
        "/api/v1/health",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["semantic_retrieval_enabled"] is True
    assert body["semantic_retrieval_status"] == "available"
    assert body["semantic_retrieval_error"] is None
    assert body["semantic_last_failure_at"] is None
    assert body["semantic_last_recovery_attempt_at"] is None
    assert body["semantic_recovery_cooldown_seconds"] == 60.0


def test_health_check_returns_cooldown_status(
    monkeypatch: MonkeyPatch,
) -> None:
    settings = Settings(
        environment="test",
        semantic_retrieval_enabled=True,
        semantic_recovery_cooldown_seconds=60.0,
    )

    failure_time = datetime(
        2026,
        7,
        29,
        18,
        0,
        tzinfo=UTC,
    )

    recovery_attempt_time = datetime(
        2026,
        7,
        29,
        18,
        1,
        tzinfo=UTC,
    )

    runtime = create_semantic_runtime_state(
        is_available=False,
        should_attempt_recovery=False,
        startup_error="provider unavailable",
        last_failure_at=failure_time,
        last_recovery_attempt_at=(recovery_attempt_time),
    )

    monkeypatch.setattr(
        health,
        "get_settings",
        lambda: settings,
    )

    monkeypatch.setattr(
        app.state,
        "semantic_runtime",
        runtime,
        raising=False,
    )

    response = client.get(
        "/api/v1/health",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["semantic_retrieval_status"] == "cooldown"
    assert body["semantic_retrieval_error"] == ("provider unavailable")
    assert (
        datetime.fromisoformat(
            body["semantic_last_failure_at"].replace(
                "Z",
                "+00:00",
            )
        )
        == failure_time
    )
    assert (
        datetime.fromisoformat(
            body["semantic_last_recovery_attempt_at"].replace(
                "Z",
                "+00:00",
            )
        )
        == recovery_attempt_time
    )


def test_health_check_returns_unavailable_status_when_recovery_is_allowed(
    monkeypatch: MonkeyPatch,
) -> None:
    settings = Settings(
        environment="test",
        semantic_retrieval_enabled=True,
        semantic_recovery_cooldown_seconds=60.0,
    )

    failure_time = datetime(
        2026,
        7,
        29,
        18,
        0,
        tzinfo=UTC,
    )

    runtime = create_semantic_runtime_state(
        is_available=False,
        should_attempt_recovery=True,
        startup_error="provider unavailable",
        last_failure_at=failure_time,
    )

    monkeypatch.setattr(
        health,
        "get_settings",
        lambda: settings,
    )

    monkeypatch.setattr(
        app.state,
        "semantic_runtime",
        runtime,
        raising=False,
    )

    response = client.get(
        "/api/v1/health",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["semantic_retrieval_status"] == "unavailable"
    assert body["semantic_retrieval_error"] == ("provider unavailable")


def test_health_check_returns_unavailable_when_runtime_is_missing(
    monkeypatch: MonkeyPatch,
) -> None:
    settings = Settings(
        environment="test",
        semantic_retrieval_enabled=True,
        semantic_recovery_cooldown_seconds=60.0,
    )

    monkeypatch.setattr(
        health,
        "get_settings",
        lambda: settings,
    )

    monkeypatch.setattr(
        app.state,
        "semantic_runtime",
        None,
        raising=False,
    )

    response = client.get(
        "/api/v1/health",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["semantic_retrieval_status"] == "unavailable"
    assert body["semantic_retrieval_error"] is None
    assert body["semantic_last_failure_at"] is None
    assert body["semantic_last_recovery_attempt_at"] is None


def test_unknown_route_returns_not_found() -> None:
    response = client.get(
        "/api/v1/does-not-exist",
    )

    assert response.status_code == 404
