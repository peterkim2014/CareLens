from datetime import UTC, date, datetime
from uuid import uuid4

from app.ai.retrieval.mappers import (
    map_evidence_document,
)
from app.db.models import (
    EvidenceDocumentModel,
    ReviewStatus,
)


def test_mapper_converts_model_to_domain_document() -> None:
    model = EvidenceDocumentModel(
        id=uuid4(),
        external_id="hypertension-guidance",
        title="Hypertension guidance",
        content=("Reviewed evidence concerning hypertension."),
        source_name="CareLens evidence library",
        source_url="https://example.com/hypertension",
        publication_date=date(
            2025,
            1,
            15,
        ),
        reviewed_at=datetime.now(UTC),
        review_status=ReviewStatus.APPROVED,
        specialty="cardiology",
        keywords=[
            "hypertension",
            "blood pressure",
        ],
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    document = map_evidence_document(model)

    assert document.document_id == model.external_id
    assert document.title == model.title
    assert document.content == model.content
    assert document.source == model.source_name
    assert document.source_type == "reviewed_evidence"
    assert document.metadata == {
        "keywords": "hypertension,blood pressure",
        "publication_date": "2025-01-15",
        "source_url": ("https://example.com/hypertension"),
        "specialty": "cardiology",
    }


def test_mapper_omits_missing_optional_metadata() -> None:
    model = EvidenceDocumentModel(
        id=uuid4(),
        external_id="fever-guidance",
        title="Fever guidance",
        content="Reviewed evidence concerning fever.",
        source_name="CareLens evidence library",
        source_url=None,
        publication_date=None,
        reviewed_at=datetime.now(UTC),
        review_status=ReviewStatus.APPROVED,
        specialty=None,
        keywords=[],
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    document = map_evidence_document(model)

    assert document.document_id == "fever-guidance"
    assert document.source == ("CareLens evidence library")
    assert document.source_type == "reviewed_evidence"
    assert document.metadata == {}


def test_mapper_creates_independent_metadata() -> None:
    model = EvidenceDocumentModel(
        id=uuid4(),
        external_id="asthma-guidance",
        title="Asthma guidance",
        content="Reviewed evidence concerning asthma.",
        source_name="CareLens evidence library",
        source_url="https://example.com/asthma",
        publication_date=None,
        reviewed_at=datetime.now(UTC),
        review_status=ReviewStatus.APPROVED,
        specialty="pulmonology",
        keywords=[
            "asthma",
        ],
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    document = map_evidence_document(model)

    document.metadata["specialty"] = "changed"

    assert model.specialty == "pulmonology"
    assert model.keywords == ["asthma"]
