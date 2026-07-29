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


@pytest.fixture
def client() -> Iterator[TestClient]:
    repository = InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="allergy-001",
                title="Seasonal allergy symptoms",
                content=(
                    "Seasonal allergies commonly cause "
                    "sneezing, nasal congestion, itchy eyes, "
                    "and a runny nose."
                ),
                source="CareLens Clinical Reference",
                source_type="clinical_reference",
                metadata={
                    "specialty": "allergy",
                },
            ),
            EvidenceDocument(
                document_id="headache-001",
                title="Common headache causes",
                content=(
                    "Common headache triggers include "
                    "dehydration, stress, insufficient sleep, "
                    "and eye strain."
                ),
                source="CareLens Clinical Reference",
                source_type="clinical_reference",
                metadata={
                    "specialty": "general medicine",
                },
            ),
        ]
    )

    retrieval_service = RetrievalService(
        repository=repository,
        minimum_score=0.1,
        maximum_results=5,
    )

    app.dependency_overrides[get_retrieval_service] = lambda: retrieval_service

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(
            get_retrieval_service,
            None,
        )


def test_risk_endpoint_returns_emergency_assessment(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/analysis/risk",
        json={
            "text": "I have severe chest pain.",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["risk_level"] == "emergency"
    assert body["routing_action"] == "seek_emergency_care"
    assert body["signals"]

    assert any(signal["code"] == "chest_pain" for signal in body["signals"])


def test_risk_endpoint_returns_routine_assessment(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/analysis/risk",
        json={
            "text": ("What symptoms do seasonal allergies cause?"),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["risk_level"] == "routine"
    assert body["routing_action"] == "continue_analysis"
    assert body["signals"] == []


def test_risk_endpoint_rejects_empty_query(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/analysis/risk",
        json={
            "text": "",
        },
    )

    assert response.status_code == 422


def test_risk_endpoint_rejects_oversized_query(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/analysis/risk",
        json={
            "text": "a" * 5001,
        },
    )

    assert response.status_code == 422


def test_analysis_pipeline_halts_emergency_query(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/analysis",
        json={
            "text": "I have severe chest pain.",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["disposition"] == "halted_emergency"
    assert body["risk_assessment"]["risk_level"] == "emergency"
    assert body["retrieval_result"] is None
    assert body["grounded_response"] is None
    assert body["grounding_validation"] is None

    user_response = body["user_response"]

    assert user_response["kind"] == "emergency"
    assert user_response["can_continue"] is False
    assert user_response["message"]
    assert user_response["recommended_actions"]

    assert body["completed_stages"] == [
        "intake_validated",
        "risk_assessed",
        "safety_routed",
        "user_response_created",
    ]

    audit = body["audit"]

    assert audit["total_duration_ms"] >= 0
    assert audit["completed_at"] >= audit["started_at"]

    assert [event["stage"] for event in audit["events"]] == body["completed_stages"]

    assert all(event["status"] == "completed" for event in audit["events"])

    assert all(event["duration_ms"] >= 0 for event in audit["events"])


def test_analysis_pipeline_generates_grounded_response(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/analysis",
        json={
            "text": ("What are common seasonal allergy symptoms?"),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["disposition"] == "response_generated"
    assert body["risk_assessment"]["risk_level"] == "routine"

    retrieval_result = body["retrieval_result"]

    assert retrieval_result is not None
    assert retrieval_result["evidence"]

    grounded_response = body["grounded_response"]

    assert grounded_response is not None
    assert "[1]" in grounded_response["answer"]
    assert grounded_response["citations"]

    assert grounded_response["citations"][0]["document_id"] == "allergy-001"

    grounding_validation = body["grounding_validation"]

    assert grounding_validation is not None
    assert grounding_validation["is_valid"] is True
    assert grounding_validation["issues"] == []

    user_response = body["user_response"]

    assert user_response["kind"] == "grounded"
    assert user_response["can_continue"] is True

    assert user_response["message"] == grounded_response["answer"]

    assert body["completed_stages"] == [
        "intake_validated",
        "risk_assessed",
        "safety_routed",
        "evidence_retrieved",
        "evidence_validated",
        "response_generated",
        "response_validated",
        "user_response_created",
    ]

    audit = body["audit"]

    assert audit["total_duration_ms"] >= 0
    assert audit["completed_at"] >= audit["started_at"]

    assert [event["stage"] for event in audit["events"]] == body["completed_stages"]

    assert all(event["status"] == "completed" for event in audit["events"])

    assert all(event["duration_ms"] >= 0 for event in audit["events"])


def test_analysis_pipeline_returns_insufficient_evidence(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/analysis",
        json={
            "text": "Explain psoriasis plaques.",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["disposition"] == "insufficient_evidence"
    assert body["risk_assessment"]["risk_level"] == "routine"

    retrieval_result = body["retrieval_result"]

    assert retrieval_result is not None
    assert retrieval_result["evidence"] == []

    assert body["grounded_response"] is None
    assert body["grounding_validation"] is None

    user_response = body["user_response"]

    assert user_response["kind"] == "insufficient_evidence"
    assert user_response["can_continue"] is True
    assert user_response["message"]
    assert user_response["recommended_actions"]

    assert body["completed_stages"] == [
        "intake_validated",
        "risk_assessed",
        "safety_routed",
        "evidence_retrieved",
        "evidence_validated",
        "user_response_created",
    ]

    audit = body["audit"]

    assert audit["total_duration_ms"] >= 0

    assert [event["stage"] for event in audit["events"]] == body["completed_stages"]

    assert all(event["status"] == "completed" for event in audit["events"])

    assert all(event["duration_ms"] >= 0 for event in audit["events"])


def test_analysis_audit_excludes_raw_query_text(
    client: TestClient,
) -> None:
    query_text = "This private medical description must not appear in the audit record."

    response = client.post(
        "/api/v1/analysis",
        json={
            "text": query_text,
        },
    )

    assert response.status_code == 200

    audit = response.json()["audit"]
    serialized_audit = str(audit)

    assert query_text not in serialized_audit
