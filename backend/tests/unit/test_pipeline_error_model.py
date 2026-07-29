from collections.abc import Iterator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.ai.retrieval import (
    InMemoryEvidenceRepository,
    RetrievalResult,
    RetrievalService,
)
from app.api.dependencies.retrieval import (
    get_retrieval_service,
)
from app.core.errors import (
    AnalysisPipelineError,
    handle_analysis_pipeline_error,
)
from app.main import app


class FailingRetrievalService(RetrievalService):
    def retrieve(
        self,
        query: str,
    ) -> RetrievalResult:
        del query

        raise RuntimeError("Database password and private failure details")


@pytest.fixture
def client() -> Iterator[TestClient]:
    repository = InMemoryEvidenceRepository(
        documents=[],
    )

    failing_service = FailingRetrievalService(
        repository,
    )

    app.dependency_overrides[get_retrieval_service] = lambda: failing_service

    with TestClient(
        app,
        raise_server_exceptions=False,
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_analysis_pipeline_handler_is_registered() -> None:
    assert AnalysisPipelineError in app.exception_handlers

    assert (
        app.exception_handlers[AnalysisPipelineError] is handle_analysis_pipeline_error
    )


def test_analysis_returns_safe_pipeline_error(
    client: TestClient,
) -> None:
    private_query = (
        "This private symptom text must not appear inside the error response."
    )
    trace_id = uuid4()

    response = client.post(
        "/api/v1/analysis",
        headers={
            "X-Trace-ID": str(trace_id),
        },
        json={
            "text": private_query,
        },
    )

    assert response.status_code == 500

    body = response.json()

    assert body["error"]["code"] == "analysis_pipeline_failed"
    assert body["error"]["message"] == (
        "The analysis could not be completed safely. Please try again."
    )
    assert body["error"]["failed_stage"] == "evidence_retrieved"
    assert body["error"]["retryable"] is True
    assert body["error"]["trace_id"] == str(trace_id)

    assert response.headers["X-Trace-ID"] == str(trace_id)

    parsed_trace_id = UUID(body["error"]["trace_id"])

    assert parsed_trace_id == trace_id

    serialized_body = response.text

    assert private_query not in serialized_body
    assert "Database password" not in serialized_body
    assert "private failure details" not in serialized_body
    assert "RuntimeError" not in serialized_body
