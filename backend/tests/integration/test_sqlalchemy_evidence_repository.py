from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.ai.retrieval.sqlalchemy_repository import (
    SQLAlchemyEvidenceRepository,
)
from app.db.base import Base
from app.db.models import (
    EvidenceDocumentModel,
    ReviewStatus,
)


@pytest.fixture
def database_engine() -> Iterator[Engine]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(engine)

    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def database_session(
    database_engine: Engine,
) -> Iterator[Session]:
    session_factory = sessionmaker(
        bind=database_engine,
        class_=Session,
        autoflush=False,
        expire_on_commit=False,
    )

    with session_factory() as session:
        yield session


def build_evidence_document(
    *,
    external_id: str,
    review_status: ReviewStatus = ReviewStatus.APPROVED,
    is_active: bool = True,
    reviewed_at: datetime | None = None,
    created_at: datetime | None = None,
) -> EvidenceDocumentModel:
    now = datetime.now(UTC)

    return EvidenceDocumentModel(
        id=uuid4(),
        external_id=external_id,
        title=f"Evidence document {external_id}",
        content=(f"Reviewed medical evidence for {external_id}."),
        source_name="CareLens reviewed evidence",
        source_url=f"https://example.com/{external_id}",
        publication_date=None,
        reviewed_at=reviewed_at,
        review_status=review_status,
        specialty="general medicine",
        keywords=[
            "medical",
            "evidence",
        ],
        is_active=is_active,
        created_at=created_at or now,
        updated_at=now,
    )


def test_repository_returns_approved_active_documents(
    database_session: Session,
) -> None:
    approved_active = build_evidence_document(
        external_id="approved-active",
    )
    approved_inactive = build_evidence_document(
        external_id="approved-inactive",
        is_active=False,
    )
    draft_active = build_evidence_document(
        external_id="draft-active",
        review_status=ReviewStatus.DRAFT,
    )
    rejected_active = build_evidence_document(
        external_id="rejected-active",
        review_status=ReviewStatus.REJECTED,
    )

    database_session.add_all(
        [
            approved_active,
            approved_inactive,
            draft_active,
            rejected_active,
        ]
    )
    database_session.commit()

    repository = SQLAlchemyEvidenceRepository(
        database_session,
    )

    documents = repository.list_searchable_documents()

    assert [document.document_id for document in documents] == [
        "approved-active",
    ]


def test_repository_maps_models_to_domain_documents(
    database_session: Session,
) -> None:
    model = build_evidence_document(
        external_id="mapped-guidance",
    )

    database_session.add(model)
    database_session.commit()

    repository = SQLAlchemyEvidenceRepository(
        database_session,
    )

    documents = repository.list_searchable_documents()

    assert len(documents) == 1

    document = documents[0]

    assert document.document_id == model.external_id
    assert document.title == model.title
    assert document.content == model.content
    assert document.source == model.source_name
    assert document.source_type == "reviewed_evidence"
    assert document.metadata == {
        "keywords": "medical,evidence",
        "source_url": ("https://example.com/mapped-guidance"),
        "specialty": "general medicine",
    }


def test_repository_returns_document_by_external_id(
    database_session: Session,
) -> None:
    model = build_evidence_document(
        external_id="fever-guidance",
    )

    database_session.add(model)
    database_session.commit()

    repository = SQLAlchemyEvidenceRepository(
        database_session,
    )

    result = repository.get_searchable_document(
        "fever-guidance",
    )

    assert result is not None
    assert result.document_id == "fever-guidance"
    assert result.title == model.title
    assert result.content == model.content
    assert result.source == model.source_name
    assert result.source_type == "reviewed_evidence"
    assert result.metadata["keywords"] == ("medical,evidence")


def test_repository_normalizes_external_id(
    database_session: Session,
) -> None:
    model = build_evidence_document(
        external_id="fever-guidance",
    )

    database_session.add(model)
    database_session.commit()

    repository = SQLAlchemyEvidenceRepository(
        database_session,
    )

    result = repository.get_searchable_document(
        "  fever-guidance  ",
    )

    assert result is not None
    assert result.document_id == "fever-guidance"


def test_repository_returns_none_for_unknown_external_id(
    database_session: Session,
) -> None:
    repository = SQLAlchemyEvidenceRepository(
        database_session,
    )

    result = repository.get_searchable_document(
        "missing-guidance",
    )

    assert result is None


def test_repository_does_not_return_inactive_document_by_id(
    database_session: Session,
) -> None:
    model = build_evidence_document(
        external_id="inactive-guidance",
        is_active=False,
    )

    database_session.add(model)
    database_session.commit()

    repository = SQLAlchemyEvidenceRepository(
        database_session,
    )

    result = repository.get_searchable_document(
        "inactive-guidance",
    )

    assert result is None


def test_repository_does_not_return_unapproved_document_by_id(
    database_session: Session,
) -> None:
    model = build_evidence_document(
        external_id="draft-guidance",
        review_status=ReviewStatus.DRAFT,
    )

    database_session.add(model)
    database_session.commit()

    repository = SQLAlchemyEvidenceRepository(
        database_session,
    )

    result = repository.get_searchable_document(
        "draft-guidance",
    )

    assert result is None


def test_repository_returns_none_for_blank_external_id(
    database_session: Session,
) -> None:
    repository = SQLAlchemyEvidenceRepository(
        database_session,
    )

    assert repository.get_searchable_document("") is None
    assert repository.get_searchable_document("   ") is None


def test_repository_applies_result_limit(
    database_session: Session,
) -> None:
    database_session.add_all(
        [
            build_evidence_document(
                external_id="document-1",
            ),
            build_evidence_document(
                external_id="document-2",
            ),
            build_evidence_document(
                external_id="document-3",
            ),
        ]
    )
    database_session.commit()

    repository = SQLAlchemyEvidenceRepository(
        database_session,
    )

    documents = repository.list_searchable_documents(
        limit=2,
    )

    assert len(documents) == 2


def test_repository_rejects_zero_limit(
    database_session: Session,
) -> None:
    repository = SQLAlchemyEvidenceRepository(
        database_session,
    )

    with pytest.raises(
        ValueError,
        match="limit must be greater than zero",
    ):
        repository.list_searchable_documents(
            limit=0,
        )


def test_repository_rejects_negative_limit(
    database_session: Session,
) -> None:
    repository = SQLAlchemyEvidenceRepository(
        database_session,
    )

    with pytest.raises(
        ValueError,
        match="limit must be greater than zero",
    ):
        repository.list_searchable_documents(
            limit=-1,
        )


def test_repository_counts_only_searchable_documents(
    database_session: Session,
) -> None:
    database_session.add_all(
        [
            build_evidence_document(
                external_id="approved-1",
            ),
            build_evidence_document(
                external_id="approved-2",
            ),
            build_evidence_document(
                external_id="inactive",
                is_active=False,
            ),
            build_evidence_document(
                external_id="draft",
                review_status=ReviewStatus.DRAFT,
            ),
        ]
    )
    database_session.commit()

    repository = SQLAlchemyEvidenceRepository(
        database_session,
    )

    assert repository.count_searchable_documents() == 2


def test_repository_returns_zero_when_no_documents_exist(
    database_session: Session,
) -> None:
    repository = SQLAlchemyEvidenceRepository(
        database_session,
    )

    assert repository.count_searchable_documents() == 0


def test_repository_orders_documents_deterministically(
    database_session: Session,
) -> None:
    newest_review = datetime(
        2026,
        7,
        20,
        tzinfo=UTC,
    )
    older_review = datetime(
        2026,
        7,
        10,
        tzinfo=UTC,
    )

    database_session.add_all(
        [
            build_evidence_document(
                external_id="older",
                reviewed_at=older_review,
            ),
            build_evidence_document(
                external_id="newer-b",
                reviewed_at=newest_review,
                created_at=datetime(
                    2026,
                    7,
                    21,
                    tzinfo=UTC,
                ),
            ),
            build_evidence_document(
                external_id="newer-a",
                reviewed_at=newest_review,
                created_at=datetime(
                    2026,
                    7,
                    22,
                    tzinfo=UTC,
                ),
            ),
        ]
    )
    database_session.commit()

    repository = SQLAlchemyEvidenceRepository(
        database_session,
    )

    documents = repository.list_searchable_documents()

    assert [document.document_id for document in documents] == [
        "newer-a",
        "newer-b",
        "older",
    ]
