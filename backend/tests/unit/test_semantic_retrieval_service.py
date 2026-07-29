from app.ai.retrieval.semantic.schemas import (
    SemanticSearchResult,
)
from app.ai.retrieval.semantic.service import (
    SemanticRetrievalService,
)


class FakeEmbedder:
    def __init__(
        self,
        *,
        embedding: list[float],
    ) -> None:
        self._embedding = embedding
        self.received_text: str | None = None
        self.received_texts: list[str] | None = None

    def embed(
        self,
        text: str,
    ) -> list[float]:
        self.received_text = text

        return list(
            self._embedding,
        )

    def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        self.received_texts = list(texts)

        return [self.embed(text) for text in texts]


class FakeVectorRepository:
    def __init__(
        self,
        results: list[SemanticSearchResult],
    ) -> None:
        self.results = results
        self.received_embedding: list[float] | None = None
        self.received_limit: int | None = None

    def search(
        self,
        embedding: list[float],
        *,
        limit: int,
    ) -> list[SemanticSearchResult]:
        self.received_embedding = embedding
        self.received_limit = limit

        return self.results[:limit]


def test_semantic_retrieval_embeds_and_searches() -> None:
    embedder = FakeEmbedder(
        embedding=[0.1, 0.2, 0.3],
    )
    repository = FakeVectorRepository(
        results=[
            SemanticSearchResult(
                document_id="allergy-001",
                similarity=0.92,
            ),
        ],
    )

    service = SemanticRetrievalService(
        embedder=embedder,
        repository=repository,
    )

    results = service.retrieve(
        "dripping nose",
        limit=5,
    )

    assert embedder.received_text == "dripping nose"
    assert repository.received_embedding == [
        0.1,
        0.2,
        0.3,
    ]
    assert repository.received_limit == 5
    assert results[0].document_id == "allergy-001"


def test_semantic_retrieval_ignores_blank_query() -> None:
    embedder = FakeEmbedder(
        embedding=[0.1],
    )
    repository = FakeVectorRepository(
        results=[],
    )

    service = SemanticRetrievalService(
        embedder=embedder,
        repository=repository,
    )

    results = service.retrieve(
        "   ",
        limit=5,
    )

    assert results == []
    assert embedder.received_text is None
    assert repository.received_embedding is None


def test_semantic_retrieval_ignores_empty_embedding() -> None:
    embedder = FakeEmbedder(
        embedding=[],
    )
    repository = FakeVectorRepository(
        results=[
            SemanticSearchResult(
                document_id="allergy-001",
                similarity=0.9,
            ),
        ],
    )

    service = SemanticRetrievalService(
        embedder=embedder,
        repository=repository,
    )

    results = service.retrieve(
        "allergy symptoms",
        limit=5,
    )

    assert results == []
    assert repository.received_embedding is None
