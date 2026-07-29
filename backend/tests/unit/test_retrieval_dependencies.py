import pytest
from fastapi import FastAPI
from starlette.requests import Request

from app.ai.retrieval import (
    InMemoryEvidenceRepository,
)
from app.ai.retrieval.semantic import (
    HashingEmbedder,
    InMemoryVectorRepository,
    SemanticIndexingService,
    SemanticRetrievalService,
    SemanticRuntime,
)
from app.ai.retrieval.semantic.schemas import (
    SemanticSearchResult,
)
from app.api.dependencies.retrieval import (
    get_retrieval_service,
    get_semantic_runtime,
    recover_semantic_runtime,
)
from app.core.config import Settings


def create_request(
    application: FastAPI,
) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "query_string": b"",
            "server": (
                "testserver",
                80,
            ),
            "client": (
                "testclient",
                50000,
            ),
            "scheme": "http",
            "app": application,
        }
    )


def create_semantic_runtime(
    *,
    available: bool = True,
    recovery_cooldown_seconds: float = 60.0,
) -> SemanticRuntime:
    evidence_repository = InMemoryEvidenceRepository(
        documents=[],
    )

    embedder = HashingEmbedder(
        dimensions=16,
    )

    vector_repository = InMemoryVectorRepository()

    indexing_service = SemanticIndexingService(
        evidence_repository=(evidence_repository),
        embedder=embedder,
        vector_repository=(vector_repository),
    )

    retrieval_service = SemanticRetrievalService(
        embedder=embedder,
        repository=vector_repository,
    )

    runtime = SemanticRuntime(
        embedder=embedder,
        vector_repository=vector_repository,
        retrieval_service=retrieval_service,
        indexing_service=indexing_service,
        recovery_cooldown_seconds=recovery_cooldown_seconds,
    )

    if available:
        runtime.synchronize_index()

    return runtime


def test_get_semantic_runtime_returns_none_when_missing() -> None:
    application = FastAPI()

    request = create_request(
        application,
    )

    assert (
        get_semantic_runtime(
            request,
        )
        is None
    )


def test_get_semantic_runtime_returns_none_when_state_is_none() -> None:
    application = FastAPI()
    application.state.semantic_runtime = None

    request = create_request(
        application,
    )

    assert (
        get_semantic_runtime(
            request,
        )
        is None
    )


def test_get_semantic_runtime_returns_application_runtime() -> None:
    application = FastAPI()
    runtime = create_semantic_runtime()

    application.state.semantic_runtime = runtime

    request = create_request(
        application,
    )

    assert (
        get_semantic_runtime(
            request,
        )
        is runtime
    )


def test_retrieval_service_builds_without_semantic_runtime() -> None:
    repository = InMemoryEvidenceRepository(
        documents=[],
    )

    settings = Settings(
        semantic_retrieval_enabled=False,
    )

    service = get_retrieval_service(
        repository=repository,
        settings=settings,
        semantic_runtime=None,
    )

    assert service is not None


def test_retrieval_service_builds_with_available_semantic_runtime() -> None:
    repository = InMemoryEvidenceRepository(
        documents=[],
    )

    settings = Settings(
        semantic_retrieval_enabled=True,
    )

    runtime = create_semantic_runtime(
        available=True,
    )

    service = get_retrieval_service(
        repository=repository,
        settings=settings,
        semantic_runtime=runtime,
    )

    assert service is not None


def test_retrieval_service_builds_with_unavailable_semantic_runtime() -> None:
    repository = InMemoryEvidenceRepository(
        documents=[],
    )

    settings = Settings(
        semantic_retrieval_enabled=True,
    )

    runtime = create_semantic_runtime(
        available=False,
    )

    runtime.mark_unavailable(
        RuntimeError(
            "embedding provider unavailable",
        )
    )

    service = get_retrieval_service(
        repository=repository,
        settings=settings,
        semantic_runtime=runtime,
    )

    assert service is not None


def test_request_time_semantic_failure_marks_runtime_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = InMemoryEvidenceRepository(
        documents=[],
    )

    settings = Settings(
        semantic_retrieval_enabled=True,
    )

    runtime = create_semantic_runtime(
        available=True,
    )

    def fail_retrieval(
        query: str,
        *,
        limit: int,
    ) -> list[SemanticSearchResult]:
        del query
        del limit

        raise RuntimeError(
            "provider unavailable",
        )

    monkeypatch.setattr(
        runtime.retrieval_service,
        "retrieve",
        fail_retrieval,
    )

    service = get_retrieval_service(
        repository=repository,
        settings=settings,
        semantic_runtime=runtime,
    )

    result = service.retrieve(
        "allergy symptoms",
    )

    assert result.evidence == []
    assert runtime.is_available is False
    assert runtime.indexing_result is None
    assert runtime.startup_error == ("provider unavailable")


def test_retrieval_dependency_recovers_semantic_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = InMemoryEvidenceRepository(
        documents=[],
    )

    settings = Settings(
        semantic_retrieval_enabled=True,
        semantic_recovery_cooldown_seconds=0.0,
    )

    runtime = create_semantic_runtime(
        available=False,
        recovery_cooldown_seconds=0.0,
    )

    recovery_attempted = False

    def recover() -> bool:
        nonlocal recovery_attempted

        recovery_attempted = True
        runtime.is_available = True

        return True

    monkeypatch.setattr(
        runtime,
        "attempt_recovery",
        recover,
    )

    recovered_runtime = recover_semantic_runtime(
        semantic_runtime=runtime,
        settings=settings,
    )

    service = get_retrieval_service(
        repository=repository,
        settings=settings,
        semantic_runtime=recovered_runtime,
    )

    assert recovery_attempted is True
    assert recovered_runtime is runtime
    assert runtime.is_available is True
    assert service is not None


def test_retrieval_dependency_skips_recovery_when_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        semantic_retrieval_enabled=True,
    )

    runtime = create_semantic_runtime(
        available=True,
    )

    def unexpected_recovery() -> bool:
        raise AssertionError(
            "Recovery should not run.",
        )

    monkeypatch.setattr(
        runtime,
        "attempt_recovery",
        unexpected_recovery,
    )

    result = recover_semantic_runtime(
        semantic_runtime=runtime,
        settings=settings,
    )

    assert result is runtime
