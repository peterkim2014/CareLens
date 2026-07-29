import pytest

from app.ai.generation import (
    GroundedResponseService,
    InsufficientEvidenceError,
)
from app.ai.intake import ClinicalQuery
from app.ai.retrieval import (
    RetrievalResult,
    RetrievedEvidence,
)


def create_retrieval_result() -> RetrievalResult:
    return RetrievalResult(
        query="What symptoms do seasonal allergies cause?",
        total_candidates=1,
        evidence=[
            RetrievedEvidence(
                document_id="allergy-001",
                title="Seasonal allergy symptoms",
                content=("Seasonal allergies commonly cause sneezing and itchy eyes."),
                source="Clinical Reference",
                source_type="clinical_reference",
                score=0.8,
                matched_terms=[
                    "allergies",
                    "seasonal",
                    "symptoms",
                ],
            )
        ],
    )


def test_service_generates_grounded_response() -> None:
    service = GroundedResponseService()

    result = service.generate(
        query=ClinicalQuery(text="What symptoms do seasonal allergies cause?"),
        retrieval_result=create_retrieval_result(),
    )

    assert "sneezing and itchy eyes" in result.answer
    assert "[1]" in result.answer
    assert len(result.citations) == 1
    assert result.citations[0].document_id == "allergy-001"


def test_service_preserves_source_information() -> None:
    service = GroundedResponseService()

    result = service.generate(
        query=ClinicalQuery(text="What symptoms do seasonal allergies cause?"),
        retrieval_result=create_retrieval_result(),
    )

    citation = result.citations[0]

    assert citation.citation_id == 1
    assert citation.title == "Seasonal allergy symptoms"
    assert citation.source == "Clinical Reference"


def test_service_includes_medical_limitation() -> None:
    service = GroundedResponseService()

    result = service.generate(
        query=ClinicalQuery(text="What symptoms do seasonal allergies cause?"),
        retrieval_result=create_retrieval_result(),
    )

    assert result.limitations
    assert "not a medical diagnosis" in result.limitations[0]


def test_service_rejects_empty_evidence() -> None:
    service = GroundedResponseService()

    retrieval_result = RetrievalResult(
        query="What causes kidney stones?",
        total_candidates=0,
        evidence=[],
    )

    with pytest.raises(
        InsufficientEvidenceError,
        match="requires at least one evidence item",
    ):
        service.generate(
            query=ClinicalQuery(text="What causes kidney stones?"),
            retrieval_result=retrieval_result,
        )
