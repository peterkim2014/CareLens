import math
from collections.abc import Iterable

from app.ai.retrieval.semantic.schemas import (
    EmbeddingRecord,
    SemanticSearchResult,
)


class InMemoryVectorRepository:
    def __init__(
        self,
        records: Iterable[EmbeddingRecord] | None = None,
    ) -> None:
        self._embeddings: dict[str, EmbeddingRecord] = {}

        if records is not None:
            self.upsert_many(
                list(records),
            )

    def clear(self) -> None:
        self._embeddings.clear()

    def count(self) -> int:
        return len(self._embeddings)

    def upsert(
        self,
        record: EmbeddingRecord,
    ) -> None:
        normalized_document_id = record.document_id.strip()

        if not normalized_document_id:
            raise ValueError(
                "document_id cannot be empty",
            )

        if not record.embedding:
            raise ValueError(
                "embedding cannot be empty",
            )

        self._embeddings[normalized_document_id] = EmbeddingRecord(
            document_id=normalized_document_id,
            embedding=list(record.embedding),
            embedding_model=record.embedding_model,
            content_hash=record.content_hash,
        )

    def upsert_many(
        self,
        records: list[EmbeddingRecord],
    ) -> None:
        for record in records:
            self.upsert(
                record,
            )

    def delete(
        self,
        document_id: str,
    ) -> bool:
        normalized_document_id = document_id.strip()

        if not normalized_document_id:
            return False

        return (
            self._embeddings.pop(
                normalized_document_id,
                None,
            )
            is not None
        )

    def delete_many(
        self,
        document_ids: set[str],
    ) -> int:
        deleted_count = 0

        for document_id in document_ids:
            if self.delete(document_id):
                deleted_count += 1

        return deleted_count

    def list_document_ids(self) -> set[str]:
        return set(
            self._embeddings,
        )

    def contains_current_embedding(
        self,
        document_id: str,
        *,
        embedding_model: str,
        content_hash: str,
    ) -> bool:
        normalized_document_id = document_id.strip()

        record = self._embeddings.get(
            normalized_document_id,
        )

        if record is None:
            return False

        return (
            record.embedding_model == embedding_model
            and record.content_hash == content_hash
        )

    def search(
        self,
        query_embedding: list[float],
        *,
        limit: int,
    ) -> list[SemanticSearchResult]:
        if limit < 1:
            raise ValueError(
                "limit must be greater than zero",
            )

        if not query_embedding:
            return []

        results: list[SemanticSearchResult] = []

        for record in self._embeddings.values():
            if len(record.embedding) != len(
                query_embedding,
            ):
                continue

            similarity = _cosine_similarity(
                query_embedding,
                record.embedding,
            )

            results.append(
                SemanticSearchResult(
                    document_id=record.document_id,
                    similarity=similarity,
                )
            )

        results.sort(
            key=lambda result: (
                -result.similarity,
                result.document_id,
            ),
        )

        return results[:limit]


def _cosine_similarity(
    left: list[float],
    right: list[float],
) -> float:
    dot_product = sum(
        left_value * right_value
        for left_value, right_value in zip(
            left,
            right,
            strict=True,
        )
    )

    left_magnitude = math.sqrt(sum(value * value for value in left))

    right_magnitude = math.sqrt(sum(value * value for value in right))

    if left_magnitude == 0.0 or right_magnitude == 0.0:
        return 0.0

    return dot_product / (left_magnitude * right_magnitude)
