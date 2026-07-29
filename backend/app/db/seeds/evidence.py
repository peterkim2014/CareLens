from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.evidence import (
    EvidenceDocumentModel,
    ReviewStatus,
)


@dataclass(frozen=True, slots=True)
class EvidenceSeedDocument:
    external_id: str
    title: str
    content: str
    source_name: str
    source_url: str | None
    publication_date: date | None
    specialty: str | None
    keywords: tuple[str, ...]
    is_active: bool = True
    review_status: ReviewStatus = ReviewStatus.APPROVED


@dataclass(frozen=True, slots=True)
class EvidenceSeedResult:
    inserted: int
    updated: int
    unchanged: int

    @property
    def total(self) -> int:
        return self.inserted + self.updated + self.unchanged


EVIDENCE_SEED_DOCUMENTS: tuple[
    EvidenceSeedDocument,
    ...,
] = (
    EvidenceSeedDocument(
        external_id="allergy-001",
        title="Seasonal allergy symptoms",
        content=(
            "Seasonal allergies commonly cause sneezing, "
            "nasal congestion, itchy eyes, and a runny nose."
        ),
        source_name="CareLens Clinical Reference",
        source_url=None,
        publication_date=None,
        specialty="allergy",
        keywords=(
            "seasonal allergies",
            "sneezing",
            "nasal congestion",
            "itchy eyes",
            "runny nose",
        ),
    ),
    EvidenceSeedDocument(
        external_id="headache-001",
        title="Common headache causes",
        content=(
            "Common headache triggers include dehydration, "
            "stress, insufficient sleep, and eye strain."
        ),
        source_name="CareLens Clinical Reference",
        source_url=None,
        publication_date=None,
        specialty="general medicine",
        keywords=(
            "headache",
            "dehydration",
            "stress",
            "sleep",
            "eye strain",
        ),
    ),
)


def seed_evidence_documents(
    session: Session,
) -> EvidenceSeedResult:
    external_ids = [document.external_id for document in EVIDENCE_SEED_DOCUMENTS]

    existing_documents = session.scalars(
        select(EvidenceDocumentModel).where(
            EvidenceDocumentModel.external_id.in_(external_ids)
        )
    ).all()

    existing_by_external_id = {
        document.external_id: document for document in existing_documents
    }

    inserted = 0
    updated = 0
    unchanged = 0

    reviewed_at = datetime.now(UTC)

    try:
        for seed_document in EVIDENCE_SEED_DOCUMENTS:
            existing_document = existing_by_external_id.get(seed_document.external_id)

            if existing_document is None:
                session.add(
                    _build_evidence_model(
                        seed_document,
                        reviewed_at=reviewed_at,
                    )
                )
                inserted += 1
                continue

            if _update_evidence_model(
                existing_document,
                seed_document,
                reviewed_at=reviewed_at,
            ):
                updated += 1
            else:
                unchanged += 1

        session.commit()
    except Exception:
        session.rollback()
        raise

    return EvidenceSeedResult(
        inserted=inserted,
        updated=updated,
        unchanged=unchanged,
    )


def _build_evidence_model(
    seed_document: EvidenceSeedDocument,
    *,
    reviewed_at: datetime,
) -> EvidenceDocumentModel:
    return EvidenceDocumentModel(
        external_id=seed_document.external_id,
        title=seed_document.title,
        content=seed_document.content,
        source_name=seed_document.source_name,
        source_url=seed_document.source_url,
        publication_date=(seed_document.publication_date),
        reviewed_at=reviewed_at,
        review_status=seed_document.review_status,
        specialty=seed_document.specialty,
        keywords=list(seed_document.keywords),
        is_active=seed_document.is_active,
    )


def _update_evidence_model(
    model: EvidenceDocumentModel,
    seed_document: EvidenceSeedDocument,
    *,
    reviewed_at: datetime,
) -> bool:
    expected_keywords = list(seed_document.keywords)

    has_changes = any(
        (
            model.title != seed_document.title,
            model.content != seed_document.content,
            model.source_name != seed_document.source_name,
            model.source_url != seed_document.source_url,
            model.publication_date != seed_document.publication_date,
            model.review_status != seed_document.review_status,
            model.specialty != seed_document.specialty,
            model.keywords != expected_keywords,
            model.is_active != seed_document.is_active,
        )
    )

    if not has_changes:
        return False

    model.title = seed_document.title
    model.content = seed_document.content
    model.source_name = seed_document.source_name
    model.source_url = seed_document.source_url
    model.publication_date = seed_document.publication_date
    model.reviewed_at = reviewed_at
    model.review_status = seed_document.review_status
    model.specialty = seed_document.specialty
    model.keywords = expected_keywords
    model.is_active = seed_document.is_active

    return True
