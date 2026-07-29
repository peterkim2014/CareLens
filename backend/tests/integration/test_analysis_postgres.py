from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.models.evidence import EvidenceDocumentModel
from app.db.seeds.evidence import seed_evidence_documents
from app.db.session import SessionFactory
from app.main import app


@pytest.fixture
def database_session() -> Iterator[Session]:
    with SessionFactory() as session:
        yield session


@pytest.fixture
def seeded_database(
    database_session: Session,
) -> Iterator[None]:
    seed_evidence_documents(database_session)

    yield

    database_session.execute(
        delete(EvidenceDocumentModel).where(
            EvidenceDocumentModel.external_id.in_(
                (
                    "allergy-001",
                    "headache-001",
                )
            )
        )
    )
    database_session.commit()


@pytest.fixture
def client(
    seeded_database: None,
) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.postgres
def test_analysis_uses_postgres_evidence(
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

    assert payload["disposition"] == "response_generated"
    assert payload["trace_id"]

    retrieval_result = payload["retrieval_result"]
    assert retrieval_result["total_candidates"] >= 1
    assert len(retrieval_result["evidence"]) >= 1

    allergy_evidence = retrieval_result["evidence"][0]
    assert allergy_evidence["document_id"] == "allergy-001"
    assert allergy_evidence["score"] > 0
    assert "sneezing" in allergy_evidence["matched_terms"]

    grounded_response = payload["grounded_response"]
    assert grounded_response["answer"]
    assert len(grounded_response["citations"]) >= 1
    assert grounded_response["citations"][0]["document_id"] == "allergy-001"

    assert payload["grounding_validation"]["is_valid"] is True

    user_response = payload["user_response"]
    assert user_response["kind"] == "grounded"
    assert user_response["message"]
    assert user_response["can_continue"] is True
