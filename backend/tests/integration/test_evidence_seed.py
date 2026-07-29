from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models.evidence import (
    EvidenceDocumentModel,
    ReviewStatus,
)
from app.db.seeds.evidence import (
    EVIDENCE_SEED_DOCUMENTS,
    seed_evidence_documents,
)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(engine)

    test_session_factory = sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )

    with test_session_factory() as test_session:
        yield test_session

    Base.metadata.drop_all(engine)
    engine.dispose()


def test_seed_inserts_evidence_documents(
    session: Session,
) -> None:
    result = seed_evidence_documents(session)

    documents = session.scalars(
        select(EvidenceDocumentModel).order_by(EvidenceDocumentModel.external_id)
    ).all()

    assert result.inserted == 2
    assert result.updated == 0
    assert result.unchanged == 0
    assert result.total == 2

    assert len(documents) == 2

    assert {document.external_id for document in documents} == {
        seed_document.external_id for seed_document in EVIDENCE_SEED_DOCUMENTS
    }

    assert all(
        document.review_status == ReviewStatus.APPROVED for document in documents
    )

    assert all(document.is_active for document in documents)

    assert all(document.reviewed_at is not None for document in documents)


def test_seed_is_idempotent(
    session: Session,
) -> None:
    first_result = seed_evidence_documents(session)
    second_result = seed_evidence_documents(session)

    documents = session.scalars(select(EvidenceDocumentModel)).all()

    assert first_result.inserted == 2

    assert second_result.inserted == 0
    assert second_result.updated == 0
    assert second_result.unchanged == 2
    assert second_result.total == 2

    assert len(documents) == 2


def test_seed_updates_existing_document(
    session: Session,
) -> None:
    existing_document = EvidenceDocumentModel(
        external_id="allergy-001",
        title="Outdated allergy title",
        content="Outdated content.",
        source_name="Outdated source",
        source_url=None,
        publication_date=None,
        reviewed_at=None,
        review_status=ReviewStatus.DRAFT,
        specialty=None,
        keywords=[],
        is_active=False,
    )

    session.add(existing_document)
    session.commit()

    result = seed_evidence_documents(session)

    updated_document = session.scalar(
        select(EvidenceDocumentModel).where(
            EvidenceDocumentModel.external_id == "allergy-001"
        )
    )

    assert updated_document is not None

    assert result.inserted == 1
    assert result.updated == 1
    assert result.unchanged == 0

    assert updated_document.title == "Seasonal allergy symptoms"
    assert updated_document.review_status == ReviewStatus.APPROVED
    assert updated_document.is_active is True
    assert updated_document.reviewed_at is not None

    assert "seasonal allergies" in (updated_document.keywords)


def test_seed_preserves_unrelated_documents(
    session: Session,
) -> None:
    unrelated_document = EvidenceDocumentModel(
        external_id="custom-document-001",
        title="Custom document",
        content="Custom evidence content.",
        source_name="Custom source",
        source_url=None,
        publication_date=None,
        reviewed_at=None,
        review_status=ReviewStatus.DRAFT,
        specialty="custom",
        keywords=["custom"],
        is_active=True,
    )

    session.add(unrelated_document)
    session.commit()

    result = seed_evidence_documents(session)

    preserved_document = session.scalar(
        select(EvidenceDocumentModel).where(
            EvidenceDocumentModel.external_id == "custom-document-001"
        )
    )

    all_documents = session.scalars(select(EvidenceDocumentModel)).all()

    assert result.inserted == 2
    assert result.updated == 0
    assert result.unchanged == 0

    assert preserved_document is not None
    assert preserved_document.title == "Custom document"

    assert len(all_documents) == 3
