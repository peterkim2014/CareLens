from datetime import date

from app.db.models import (
    EvidenceDocumentModel,
    ReviewStatus,
)


def test_evidence_document_accepts_required_fields() -> None:
    document = EvidenceDocumentModel(
        external_id="allergy-001",
        title="Seasonal allergy symptoms",
        content=(
            "Seasonal allergies may cause sneezing, nasal congestion, and itchy eyes."
        ),
        source_name="CareLens reviewed evidence",
        publication_date=date(2026, 1, 1),
        specialty="allergy",
        keywords=[
            "allergy",
            "sneezing",
            "nasal congestion",
        ],
    )

    assert document.external_id == "allergy-001"
    assert document.title == "Seasonal allergy symptoms"
    assert document.specialty == "allergy"
    assert document.keywords == [
        "allergy",
        "sneezing",
        "nasal congestion",
    ]


def test_evidence_document_accepts_review_state() -> None:
    document = EvidenceDocumentModel(
        external_id="fever-001",
        title="Fever assessment",
        content=("Fever may have infectious and noninfectious causes."),
        source_name="CareLens reviewed evidence",
        review_status=ReviewStatus.APPROVED,
        is_active=True,
        keywords=["fever"],
    )

    assert document.review_status is ReviewStatus.APPROVED
    assert document.is_active is True
