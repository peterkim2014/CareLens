from typing import Protocol

from app.ai.retrieval.semantic.schemas import (
    SemanticSearchResult,
)


class SemanticRetriever(Protocol):
    def retrieve(
        self,
        query: str,
        *,
        limit: int,
    ) -> list[SemanticSearchResult]: ...
