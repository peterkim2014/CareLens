from fastapi import FastAPI
from starlette.requests import Request

from app.ai.retrieval import (
    InMemoryEvidenceRepository,
)
from app.ai.retrieval.semantic import (
    HashingEmbedder,
    InMemoryVectorRepository,
    SemanticIndexingResult,
    SemanticIndexingService,
    SemanticRetrievalService,
    SemanticRuntime,
)
from app.api.dependencies.retrieval import (
    get_retrieval_service,
    get_semantic_runtime,
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


def create_semantic_runtime() -> SemanticRuntime:
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

    return SemanticRuntime(
        embedder=embedder,
        vector_repository=vector_repository,
        retrieval_service=retrieval_service,
        indexing_service=indexing_service,
        indexing_result=(
            SemanticIndexingResult(
                total_documents=0,
                indexed_documents=0,
                skipped_documents=0,
            )
        ),
    )


def test_get_semantic_runtime_returns_none_when_missing() -> None:
    application = FastAPI()
    request = create_request(
        application,
    )

    assert get_semantic_runtime(request) is None


def test_get_semantic_runtime_returns_application_runtime() -> None:
    application = FastAPI()
    runtime = create_semantic_runtime()

    application.state.semantic_runtime = runtime

    request = create_request(
        application,
    )

    assert get_semantic_runtime(request) is runtime


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


def test_retrieval_service_builds_with_semantic_runtime() -> None:
    repository = InMemoryEvidenceRepository(
        documents=[],
    )
    settings = Settings(
        semantic_retrieval_enabled=True,
    )
    runtime = create_semantic_runtime()

    service = get_retrieval_service(
        repository=repository,
        settings=settings,
        semantic_runtime=runtime,
    )

    assert service is not None
