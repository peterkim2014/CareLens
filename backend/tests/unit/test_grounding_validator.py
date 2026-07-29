from app.ai.generation import (
    EvidenceCitation,
    GroundedResponse,
)
from app.ai.retrieval import (
    RetrievalResult,
    RetrievedEvidence,
)
from app.ai.validation import (
    GroundingIssueCode,
    GroundingValidator,
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


def create_grounded_response() -> GroundedResponse:
    return GroundedResponse(
        answer=("Seasonal allergies commonly cause sneezing and itchy eyes. [1]"),
        citations=[
            EvidenceCitation(
                citation_id=1,
                document_id="allergy-001",
                title="Seasonal allergy symptoms",
                source="Clinical Reference",
            )
        ],
        limitations=["This response is not a medical diagnosis."],
    )


def test_validator_accepts_valid_grounded_response() -> None:
    validator = GroundingValidator()

    result = validator.validate(
        response=create_grounded_response(),
        retrieval_result=create_retrieval_result(),
    )

    assert result.is_valid is True
    assert result.issues == []


def test_validator_rejects_missing_citations() -> None:
    validator = GroundingValidator()

    response = GroundedResponse(
        answer="Seasonal allergies may cause sneezing.",
        citations=[],
        limitations=[],
    )

    result = validator.validate(
        response=response,
        retrieval_result=create_retrieval_result(),
    )

    assert result.is_valid is False
    assert result.issues[0].code is GroundingIssueCode.NO_CITATIONS


def test_validator_rejects_unknown_document() -> None:
    validator = GroundingValidator()

    response = GroundedResponse(
        answer="Seasonal allergies may cause sneezing. [1]",
        citations=[
            EvidenceCitation(
                citation_id=1,
                document_id="invented-document",
                title="Invented evidence",
                source="Unknown",
            )
        ],
        limitations=[],
    )

    result = validator.validate(
        response=response,
        retrieval_result=create_retrieval_result(),
    )

    assert result.is_valid is False
    assert any(
        issue.code is GroundingIssueCode.UNKNOWN_DOCUMENT for issue in result.issues
    )


def test_validator_rejects_missing_inline_marker() -> None:
    validator = GroundingValidator()

    response = create_grounded_response().model_copy(
        update={
            "answer": ("Seasonal allergies commonly cause sneezing and itchy eyes.")
        }
    )

    result = validator.validate(
        response=response,
        retrieval_result=create_retrieval_result(),
    )

    assert result.is_valid is False
    assert any(
        issue.code is GroundingIssueCode.MISSING_INLINE_CITATION
        for issue in result.issues
    )


def test_validator_rejects_unknown_inline_marker() -> None:
    validator = GroundingValidator()

    response = create_grounded_response().model_copy(
        update={"answer": ("Seasonal allergies commonly cause sneezing. [1] [2]")}
    )

    result = validator.validate(
        response=response,
        retrieval_result=create_retrieval_result(),
    )

    assert result.is_valid is False
    assert any(
        issue.code is GroundingIssueCode.UNKNOWN_INLINE_CITATION
        for issue in result.issues
    )


def test_validator_rejects_non_sequential_citation_ids() -> None:
    validator = GroundingValidator()

    response = GroundedResponse(
        answer="Seasonal allergies may cause sneezing. [2]",
        citations=[
            EvidenceCitation(
                citation_id=2,
                document_id="allergy-001",
                title="Seasonal allergy symptoms",
                source="Clinical Reference",
            )
        ],
        limitations=[],
    )

    result = validator.validate(
        response=response,
        retrieval_result=create_retrieval_result(),
    )

    assert result.is_valid is False
    assert any(
        issue.code is GroundingIssueCode.NON_SEQUENTIAL_CITATION_ID
        for issue in result.issues
    )
