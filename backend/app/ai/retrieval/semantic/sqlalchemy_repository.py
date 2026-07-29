from collections.abc import Callable

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.ai.retrieval.semantic.schemas import (
    EmbeddingRecord,
    SemanticSearchResult,
)
from app.db.models.evidence_embedding import (
    EvidenceEmbeddingModel,
)


class SQLAlchemyVectorRepository:
    def __init__(
        self,
        session_factory: Callable[[], Session],
    ) -> None:
        self._session_factory = session_factory

    def clear(self) -> None:
        statement = delete(
            EvidenceEmbeddingModel,
        )

        with self._session_factory() as session:
            try:
                session.execute(
                    statement,
                )
                session.commit()
            except Exception:
                session.rollback()
                raise

    def list_document_ids(self) -> set[str]:
        statement = select(
            EvidenceEmbeddingModel.document_id,
        )

        with self._session_factory() as session:
            document_ids = session.execute(
                statement,
            ).scalars()

            return set(document_ids)

    def count(self) -> int:
        statement = select(
            func.count(
                EvidenceEmbeddingModel.document_id,
            )
        )

        with self._session_factory() as session:
            return session.execute(
                statement,
            ).scalar_one()

    def delete_many(
        self,
        document_ids: set[str],
    ) -> int:
        if not document_ids:
            return 0

        statement = (
            delete(
                EvidenceEmbeddingModel,
            )
            .where(
                EvidenceEmbeddingModel.document_id.in_(
                    document_ids,
                )
            )
            .returning(
                EvidenceEmbeddingModel.document_id,
            )
        )

        with self._session_factory() as session:
            try:
                deleted_document_ids = (
                    session.execute(
                        statement,
                    )
                    .scalars()
                    .all()
                )

                session.commit()
            except Exception:
                session.rollback()
                raise

        return len(deleted_document_ids)

    def upsert(
        self,
        record: EmbeddingRecord,
    ) -> None:
        self.upsert_many(
            [record],
        )

    def upsert_many(
        self,
        records: list[EmbeddingRecord],
    ) -> None:
        if not records:
            return

        values = [
            {
                "document_id": record.document_id,
                "embedding": record.embedding,
                "embedding_model": record.embedding_model,
                "content_hash": record.content_hash,
            }
            for record in records
        ]

        insert_statement = insert(
            EvidenceEmbeddingModel,
        ).values(
            values,
        )

        upsert_statement = insert_statement.on_conflict_do_update(
            index_elements=[
                EvidenceEmbeddingModel.document_id,
            ],
            set_={
                "embedding": (insert_statement.excluded.embedding),
                "embedding_model": (insert_statement.excluded.embedding_model),
                "content_hash": (insert_statement.excluded.content_hash),
                "updated_at": func.now(),
            },
        )

        with self._session_factory() as session:
            try:
                session.execute(
                    upsert_statement,
                )
                session.commit()
            except Exception:
                session.rollback()
                raise

    def delete(
        self,
        document_id: str,
    ) -> bool:
        statement = (
            delete(
                EvidenceEmbeddingModel,
            )
            .where(
                EvidenceEmbeddingModel.document_id == document_id,
            )
            .returning(
                EvidenceEmbeddingModel.document_id,
            )
        )

        with self._session_factory() as session:
            try:
                deleted_document_id = session.execute(
                    statement,
                ).scalar_one_or_none()

                session.commit()
            except Exception:
                session.rollback()
                raise

        return deleted_document_id is not None

    def search(
        self,
        query_embedding: list[float],
        *,
        limit: int,
    ) -> list[SemanticSearchResult]:
        if limit < 1:
            raise ValueError(
                "limit must be at least 1.",
            )

        cosine_distance = EvidenceEmbeddingModel.embedding.cosine_distance(
            query_embedding,
        )

        statement = (
            select(
                EvidenceEmbeddingModel.document_id,
                cosine_distance.label(
                    "cosine_distance",
                ),
            )
            .order_by(
                cosine_distance,
            )
            .limit(
                limit,
            )
        )

        with self._session_factory() as session:
            rows = session.execute(
                statement,
            ).all()

        return [
            SemanticSearchResult(
                document_id=document_id,
                similarity=1.0 - float(distance),
            )
            for document_id, distance in rows
        ]

    def contains_current_embedding(
        self,
        document_id: str,
        *,
        embedding_model: str,
        content_hash: str,
    ) -> bool:
        statement = (
            select(
                EvidenceEmbeddingModel.document_id,
            )
            .where(
                EvidenceEmbeddingModel.document_id == document_id,
                EvidenceEmbeddingModel.embedding_model == embedding_model,
                EvidenceEmbeddingModel.content_hash == content_hash,
            )
            .limit(
                1,
            )
        )

        with self._session_factory() as session:
            stored_document_id = session.execute(
                statement,
            ).scalar_one_or_none()

        return stored_document_id is not None
