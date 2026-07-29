from collections.abc import Sequence

import pytest

from app.ai.retrieval.schemas import EvidenceDocument
from app.ai.retrieval.semantic.in_memory_repository import (
    InMemoryVectorRepository,
)
from app.ai.retrieval.semantic.indexing import (
    SemanticIndexingService,
)


class FakeEvidenceRepository:
    def __init__(
        self,
        documents: Sequence[EvidenceDocument],
    ) -> None:
        self._documents = list(documents)

    def list_documents(
        self,
    ) -> list[EvidenceDocument]:
        return list(self._documents)


class RecordingEmbedder:
    def __init__(
        self,
        *,
        model_name: str = "test-embedder",
        dimensions: int = 3,
    ) -> None:
        self._model_name = model_name
        self._dimensions = dimensions
        self.calls: list[list[str]] = []

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed(
        self,
        text: str,
    ) -> list[float]:
        return self.embed_many(
            [text],
        )[0]

    def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        self.calls.append(
            list(texts),
        )

        return [
            self._create_embedding(
                text,
            )
            for text in texts
        ]

    def _create_embedding(
        self,
        text: str,
    ) -> list[float]:
        base_value = float(
            max(
                len(text),
                1,
            )
        )

        return [
            base_value + float(index)
            for index in range(
                self._dimensions,
            )
        ]


class InvalidCountEmbedder:
    @property
    def model_name(self) -> str:
        return "invalid-count-embedder"

    def embed(
        self,
        text: str,
    ) -> list[float]:
        return [1.0, 0.0, 0.0]

    def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        return [[1.0, 0.0, 0.0]]


class EmptyEmbeddingEmbedder:
    @property
    def model_name(self) -> str:
        return "empty-embedder"

    def embed(
        self,
        text: str,
    ) -> list[float]:
        return []

    def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return [[] for _ in texts]


def create_test_document(
    *,
    document_id: str,
    title: str = "Seasonal allergies",
    content: str = (
        "Seasonal allergies can cause sneezing, congestion, and itchy eyes."
    ),
    source: str = "Test medical reference",
    source_type: str = "test",
) -> EvidenceDocument:
    return EvidenceDocument(
        document_id=document_id,
        title=title,
        content=content,
        source=source,
        source_type=source_type,
    )


def create_service(
    *,
    documents: Sequence[EvidenceDocument],
    embedder: RecordingEmbedder,
    repository: InMemoryVectorRepository | None = None,
    batch_size: int = 10,
) -> SemanticIndexingService:
    return SemanticIndexingService(
        evidence_repository=FakeEvidenceRepository(
            documents,
        ),
        vector_repository=(
            repository if repository is not None else InMemoryVectorRepository()
        ),
        embedder=embedder,
        batch_size=batch_size,
    )


def test_indexing_creates_embeddings() -> None:
    documents = [
        create_test_document(
            document_id="allergy-001",
        ),
        create_test_document(
            document_id="asthma-001",
            title="Asthma",
            content=("Asthma can cause wheezing, coughing, and shortness of breath."),
        ),
    ]
    embedder = RecordingEmbedder()
    repository = InMemoryVectorRepository()

    service = create_service(
        documents=documents,
        embedder=embedder,
        repository=repository,
    )

    result = service.rebuild_index()

    assert result.total_documents == 2
    assert result.indexed_documents == 2
    assert result.skipped_documents == 0

    assert repository.count() == 2
    assert repository.list_document_ids() == {
        "allergy-001",
        "asthma-001",
    }

    assert len(embedder.calls) == 1
    assert len(embedder.calls[0]) == 2


def test_indexing_processes_documents_in_batches() -> None:
    documents = [
        create_test_document(
            document_id=f"document-{index}",
            title=f"Document {index}",
            content=f"Evidence content {index}",
        )
        for index in range(5)
    ]
    embedder = RecordingEmbedder()
    repository = InMemoryVectorRepository()

    service = create_service(
        documents=documents,
        embedder=embedder,
        repository=repository,
        batch_size=2,
    )

    result = service.rebuild_index()

    assert result.total_documents == 5
    assert result.indexed_documents == 5
    assert result.skipped_documents == 0

    assert repository.count() == 5

    assert [len(call) for call in embedder.calls] == [
        2,
        2,
        1,
    ]


def test_indexing_empty_repository() -> None:
    embedder = RecordingEmbedder()
    repository = InMemoryVectorRepository()

    service = create_service(
        documents=[],
        embedder=embedder,
        repository=repository,
    )

    result = service.rebuild_index()

    assert result.total_documents == 0
    assert result.indexed_documents == 0
    assert result.skipped_documents == 0

    assert repository.count() == 0
    assert embedder.calls == []


def test_indexing_rejects_invalid_batch_size() -> None:
    with pytest.raises(
        ValueError,
        match="batch_size",
    ):
        SemanticIndexingService(
            evidence_repository=FakeEvidenceRepository(
                [],
            ),
            vector_repository=InMemoryVectorRepository(),
            embedder=RecordingEmbedder(),
            batch_size=0,
        )


def test_indexing_rejects_unexpected_embedding_count() -> None:
    service = SemanticIndexingService(
        evidence_repository=FakeEvidenceRepository(
            [
                create_test_document(
                    document_id="allergy-001",
                ),
                create_test_document(
                    document_id="asthma-001",
                ),
            ],
        ),
        vector_repository=InMemoryVectorRepository(),
        embedder=InvalidCountEmbedder(),
        batch_size=10,
    )

    with pytest.raises(
        RuntimeError,
        match="unexpected number",
    ):
        service.rebuild_index()


def test_indexing_skips_empty_embeddings() -> None:
    repository = InMemoryVectorRepository()

    service = SemanticIndexingService(
        evidence_repository=FakeEvidenceRepository(
            [
                create_test_document(
                    document_id="allergy-001",
                ),
            ],
        ),
        vector_repository=repository,
        embedder=EmptyEmbeddingEmbedder(),
        batch_size=10,
    )

    result = service.rebuild_index()

    assert result.total_documents == 1
    assert result.indexed_documents == 0
    assert result.skipped_documents == 1
    assert repository.count() == 0


def test_indexing_skips_current_embeddings() -> None:
    document = create_test_document(
        document_id="allergy-001",
    )
    embedder = RecordingEmbedder(
        model_name="test-model",
    )
    repository = InMemoryVectorRepository()

    service = create_service(
        documents=[
            document,
        ],
        embedder=embedder,
        repository=repository,
    )

    first_result = service.rebuild_index()
    second_result = service.rebuild_index()

    assert first_result.total_documents == 1
    assert first_result.indexed_documents == 1
    assert first_result.skipped_documents == 0

    assert second_result.total_documents == 1
    assert second_result.indexed_documents == 0
    assert second_result.skipped_documents == 1

    assert repository.count() == 1
    assert repository.list_document_ids() == {
        "allergy-001",
    }

    assert len(embedder.calls) == 1
    assert len(embedder.calls[0]) == 1


def test_indexing_reindexes_changed_documents() -> None:
    original_document = create_test_document(
        document_id="allergy-001",
        content="Original allergy evidence.",
    )
    changed_document = create_test_document(
        document_id="allergy-001",
        content="Updated allergy evidence.",
    )

    repository = InMemoryVectorRepository()
    embedder = RecordingEmbedder(
        model_name="test-model",
    )

    original_service = create_service(
        documents=[
            original_document,
        ],
        embedder=embedder,
        repository=repository,
    )

    original_result = original_service.rebuild_index()

    changed_service = create_service(
        documents=[
            changed_document,
        ],
        embedder=embedder,
        repository=repository,
    )

    changed_result = changed_service.rebuild_index()

    assert original_result.indexed_documents == 1
    assert original_result.skipped_documents == 0

    assert changed_result.total_documents == 1
    assert changed_result.indexed_documents == 1
    assert changed_result.skipped_documents == 0

    assert repository.count() == 1
    assert repository.list_document_ids() == {
        "allergy-001",
    }

    assert len(embedder.calls) == 2
    assert embedder.calls[0] != embedder.calls[1]


def test_indexing_deletes_stale_embeddings() -> None:
    allergy_document = create_test_document(
        document_id="allergy-001",
    )
    asthma_document = create_test_document(
        document_id="asthma-001",
        title="Asthma",
        content=("Asthma can cause wheezing, coughing, and shortness of breath."),
    )

    repository = InMemoryVectorRepository()
    embedder = RecordingEmbedder(
        model_name="test-model",
    )

    initial_service = create_service(
        documents=[
            allergy_document,
            asthma_document,
        ],
        embedder=embedder,
        repository=repository,
    )

    initial_result = initial_service.rebuild_index()

    assert initial_result.indexed_documents == 2
    assert repository.count() == 2

    updated_service = create_service(
        documents=[
            allergy_document,
        ],
        embedder=embedder,
        repository=repository,
    )

    updated_result = updated_service.rebuild_index()

    assert updated_result.total_documents == 1
    assert updated_result.indexed_documents == 0
    assert updated_result.skipped_documents == 1

    assert repository.count() == 1
    assert repository.list_document_ids() == {
        "allergy-001",
    }

    assert len(embedder.calls) == 1


def test_indexing_deletes_all_stale_embeddings() -> None:
    repository = InMemoryVectorRepository()
    embedder = RecordingEmbedder(
        model_name="test-model",
    )

    initial_service = create_service(
        documents=[
            create_test_document(
                document_id="allergy-001",
            ),
            create_test_document(
                document_id="asthma-001",
            ),
        ],
        embedder=embedder,
        repository=repository,
    )

    initial_service.rebuild_index()

    assert repository.count() == 2

    empty_service = create_service(
        documents=[],
        embedder=embedder,
        repository=repository,
    )

    result = empty_service.rebuild_index()

    assert result.total_documents == 0
    assert result.indexed_documents == 0
    assert result.skipped_documents == 0

    assert repository.count() == 0
    assert repository.list_document_ids() == set()


def test_indexing_reindexes_when_model_changes() -> None:
    document = create_test_document(
        document_id="allergy-001",
    )
    repository = InMemoryVectorRepository()

    first_embedder = RecordingEmbedder(
        model_name="model-a",
    )

    first_service = create_service(
        documents=[
            document,
        ],
        embedder=first_embedder,
        repository=repository,
    )

    first_result = first_service.rebuild_index()

    second_embedder = RecordingEmbedder(
        model_name="model-b",
    )

    second_service = create_service(
        documents=[
            document,
        ],
        embedder=second_embedder,
        repository=repository,
    )

    second_result = second_service.rebuild_index()

    assert first_result.indexed_documents == 1
    assert first_result.skipped_documents == 0

    assert second_result.total_documents == 1
    assert second_result.indexed_documents == 1
    assert second_result.skipped_documents == 0

    assert repository.count() == 1
    assert repository.list_document_ids() == {
        "allergy-001",
    }

    assert len(first_embedder.calls) == 1
    assert len(second_embedder.calls) == 1


def test_indexing_skips_after_model_change_is_indexed() -> None:
    document = create_test_document(
        document_id="allergy-001",
    )
    repository = InMemoryVectorRepository()

    first_service = create_service(
        documents=[
            document,
        ],
        embedder=RecordingEmbedder(
            model_name="model-a",
        ),
        repository=repository,
    )
    first_service.rebuild_index()

    second_embedder = RecordingEmbedder(
        model_name="model-b",
    )
    second_service = create_service(
        documents=[
            document,
        ],
        embedder=second_embedder,
        repository=repository,
    )

    first_model_b_result = second_service.rebuild_index()
    second_model_b_result = second_service.rebuild_index()

    assert first_model_b_result.indexed_documents == 1
    assert first_model_b_result.skipped_documents == 0

    assert second_model_b_result.indexed_documents == 0
    assert second_model_b_result.skipped_documents == 1

    assert repository.count() == 1
    assert len(second_embedder.calls) == 1
