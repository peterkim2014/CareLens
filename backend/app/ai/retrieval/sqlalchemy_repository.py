from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.ai.retrieval.mappers import map_evidence_document
from app.ai.retrieval.repository_protocol import (
    EvidenceRepository,
)
from app.ai.retrieval.schemas import EvidenceDocument
from app.db.models import (
    EvidenceDocumentModel,
    ReviewStatus,
)


class SQLAlchemyEvidenceRepository:
    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def list_documents(self) -> list[EvidenceDocument]:
        return self.list_searchable_documents()

    def list_searchable_documents(
        self,
        *,
        limit: int | None = None,
    ) -> list[EvidenceDocument]:
        self._validate_limit(limit)

        statement = self._searchable_documents_statement()

        if limit is not None:
            statement = statement.limit(limit)

        models = self._session.scalars(
            statement,
        ).all()

        return [map_evidence_document(model) for model in models]

    def get_searchable_document(
        self,
        external_id: str,
    ) -> EvidenceDocument | None:
        normalized_external_id = external_id.strip()

        if not normalized_external_id:
            return None

        statement = (
            self._searchable_documents_statement()
            .where(
                EvidenceDocumentModel.external_id == normalized_external_id,
            )
            .limit(1)
        )

        model = self._session.scalars(
            statement,
        ).first()

        if model is None:
            return None

        return map_evidence_document(model)

    def count_searchable_documents(self) -> int:
        statement = (
            select(func.count())
            .select_from(EvidenceDocumentModel)
            .where(
                *self._searchable_conditions(),
            )
        )

        count = self._session.scalar(statement)

        if count is None:
            return 0

        return count

    @staticmethod
    def _searchable_documents_statement() -> Select[tuple[EvidenceDocumentModel]]:
        return (
            select(EvidenceDocumentModel)
            .where(
                *SQLAlchemyEvidenceRepository._searchable_conditions(),
            )
            .order_by(
                EvidenceDocumentModel.reviewed_at.desc(),
                EvidenceDocumentModel.created_at.desc(),
                EvidenceDocumentModel.external_id.asc(),
            )
        )

    @staticmethod
    def _searchable_conditions() -> tuple[
        ColumnElement[bool],
        ...,
    ]:
        return (
            EvidenceDocumentModel.is_active.is_(True),
            EvidenceDocumentModel.review_status == ReviewStatus.APPROVED,
        )

    @staticmethod
    def _validate_limit(
        limit: int | None,
    ) -> None:
        if limit is None:
            return

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero",
            )


def _verify_repository_contract(
    repository: SQLAlchemyEvidenceRepository,
) -> EvidenceRepository:
    return repository
