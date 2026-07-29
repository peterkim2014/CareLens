from typing import Protocol

from app.ai.retrieval.semantic.schemas import (
    EmbeddingRecord,
    SemanticSearchResult,
)


class VectorRepository(Protocol):
    def clear(self) -> None:
        """Remove all stored embeddings."""
        ...

    def upsert(
        self,
        record: EmbeddingRecord,
    ) -> None:
        """Insert or update one embedding."""
        ...

    def upsert_many(
        self,
        records: list[EmbeddingRecord],
    ) -> None:
        """Insert or update multiple embeddings."""
        ...

    def delete(
        self,
        document_id: str,
    ) -> bool:
        """Delete an embedding by document ID."""
        ...

    def search(
        self,
        query_embedding: list[float],
        *,
        limit: int,
    ) -> list[SemanticSearchResult]:
        """Return the closest semantic matches."""
        ...


# Backward-compatible name used by service.py and __init__.py.
VectorSearchRepository = VectorRepository
