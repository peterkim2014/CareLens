from app.ai.retrieval.semantic.embedder_protocol import (
    Embedder,
)
from app.ai.retrieval.semantic.repository_protocol import (
    VectorSearchRepository,
)
from app.ai.retrieval.semantic.schemas import (
    SemanticSearchResult,
)


class SemanticRetrievalService:
    def __init__(
        self,
        *,
        embedder: Embedder,
        repository: VectorSearchRepository,
    ) -> None:
        self._embedder = embedder
        self._repository = repository

    def retrieve(
        self,
        query: str,
        *,
        limit: int,
    ) -> list[SemanticSearchResult]:
        normalized_query = query.strip()

        if not normalized_query:
            return []

        if limit < 1:
            raise ValueError(
                "limit must be at least 1.",
            )

        embedding = self._embedder.embed(
            normalized_query,
        )

        if not embedding:
            return []

        return self._repository.search(
            embedding,
            limit=limit,
        )
