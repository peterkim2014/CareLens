import math

from app.ai.retrieval.semantic.schemas import (
    EmbeddingRecord,
    SemanticSearchResult,
)


class InMemoryVectorRepository:
    def __init__(
        self,
        records: list[EmbeddingRecord] | None = None,
    ) -> None:
        self._embeddings: dict[str, list[float]] = {}

        if records is not None:
            self.upsert_many(records)

    def upsert(
        self,
        record: EmbeddingRecord,
    ) -> None:
        normalized_document_id = record.document_id.strip()

        if not normalized_document_id:
            raise ValueError(
                "document_id cannot be blank.",
            )

        self._validate_embedding(
            record.embedding,
        )

        self._embeddings[normalized_document_id] = list(
            record.embedding,
        )

    def upsert_many(
        self,
        records: list[EmbeddingRecord],
    ) -> None:
        for record in records:
            self.upsert(record)

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

    def clear(self) -> None:
        self._embeddings.clear()

    def count(self) -> int:
        return len(self._embeddings)

    def search(
        self,
        embedding: list[float],
        *,
        limit: int,
    ) -> list[SemanticSearchResult]:
        if limit < 1:
            raise ValueError(
                "limit must be at least 1.",
            )

        self._validate_embedding(
            embedding,
        )

        results: list[SemanticSearchResult] = []

        for document_id, stored_embedding in self._embeddings.items():
            if len(stored_embedding) != len(embedding):
                continue

            cosine_similarity = _cosine_similarity(
                embedding,
                stored_embedding,
            )

            normalized_score = max(
                0.0,
                min(
                    (cosine_similarity + 1.0) / 2.0,
                    1.0,
                ),
            )

            results.append(
                SemanticSearchResult(
                    document_id=document_id,
                    similarity=normalized_score,
                )
            )

        results.sort(
            key=lambda result: (
                -result.similarity,
                result.document_id,
            ),
        )

        return results[:limit]

    @staticmethod
    def _validate_embedding(
        embedding: list[float],
    ) -> None:
        if not embedding:
            raise ValueError(
                "embedding cannot be empty.",
            )

        if not all(math.isfinite(value) for value in embedding):
            raise ValueError(
                "embedding values must be finite.",
            )


def _cosine_similarity(
    first: list[float],
    second: list[float],
) -> float:
    dot_product = sum(
        first_value * second_value
        for first_value, second_value in zip(
            first,
            second,
            strict=True,
        )
    )

    first_magnitude = math.sqrt(sum(value * value for value in first))
    second_magnitude = math.sqrt(sum(value * value for value in second))

    if first_magnitude == 0.0 or second_magnitude == 0.0:
        return 0.0

    return dot_product / (first_magnitude * second_magnitude)
