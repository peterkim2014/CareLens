from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.ai.retrieval.repository import (
    InMemoryEvidenceRepository,
)
from app.ai.retrieval.schemas import EvidenceDocument
from app.ai.retrieval.service import RetrievalService
from app.api.dependencies.retrieval import (
    get_retrieval_service,
)
from app.main import app


def build_test_retrieval_service() -> RetrievalService:
    repository = InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="allergy-test-001",
                title="Seasonal allergy symptoms",
                content=(
                    "Seasonal allergies commonly cause "
                    "sneezing, nasal congestion, itchy eyes, "
                    "and a runny nose."
                ),
                source="CareLens Test Reference",
                source_type="test_reference",
                metadata={
                    "specialty": "allergy",
                },
            ),
            EvidenceDocument(
                document_id="headache-test-001",
                title="Common headache causes",
                content=(
                    "Common headache triggers include "
                    "dehydration, stress, insufficient sleep, "
                    "and eye strain."
                ),
                source="CareLens Test Reference",
                source_type="test_reference",
                metadata={
                    "specialty": "general medicine",
                },
            ),
        ]
    )

    return RetrievalService(
        repository=repository,
        minimum_score=0.1,
        maximum_results=5,
    )


@pytest.fixture
def retrieval_service() -> RetrievalService:
    return build_test_retrieval_service()


@pytest.fixture
def client(
    retrieval_service: RetrievalService,
) -> Iterator[TestClient]:
    app.dependency_overrides[get_retrieval_service] = lambda: retrieval_service

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(
            get_retrieval_service,
            None,
        )


def test_retrieval_service_dependency_can_be_overridden(
    client: TestClient,
    retrieval_service: RetrievalService,
) -> None:
    dependency = app.dependency_overrides[get_retrieval_service]

    assert dependency() is retrieval_service


def test_analysis_route_uses_overridden_retrieval_service(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/analysis",
        json={
            "text": ("I have sneezing, itchy eyes, and a runny nose."),
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert isinstance(payload, dict)
