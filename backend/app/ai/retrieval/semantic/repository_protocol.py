from typing import Protocol

from app.ai.retrieval.semantic.schemas import (
    EmbeddingRecord,
    SemanticSearchResult,
)


class VectorSearchRepository(Protocol):
    def search(
        self,
        query_embedding: list[float],
        *,
        limit: int,
    ) -> list[SemanticSearchResult]:
        """Return the closest semantic matches."""
        ...


class VectorRepository(
    VectorSearchRepository,
    Protocol,
):
    def clear(self) -> None:
        """Remove every stored embedding."""
        ...

    def count(self) -> int:
        """Return the number of stored embeddings."""
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
        """Delete one embedding."""
        ...

    def delete_many(
        self,
        document_ids: set[str],
    ) -> int:
        """Delete multiple embeddings."""
        ...

    def list_document_ids(self) -> set[str]:
        """Return every indexed document ID."""
        ...

    def contains_current_embedding(
        self,
        document_id: str,
        *,
        embedding_model: str,
        content_hash: str,
    ) -> bool:
        """Determine whether an unchanged embedding exists."""
        ...
