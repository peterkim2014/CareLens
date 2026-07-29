from typing import cast

import pytest

from app.ai.retrieval import (
    EvidenceDocument,
    InMemoryEvidenceRepository,
)
from app.ai.retrieval.semantic import (
    Embedder,
    HashingEmbedder,
    InMemoryVectorRepository,
    SemanticIndexingService,
)


class RecordingEmbedder:
    def __init__(self) -> None:
        self.batches: list[list[str]] = []

    def embed(
        self,
        text: str,
    ) -> list[float]:
        return [
            1.0,
            0.0,
        ]

    def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        self.batches.append(
            list(texts),
        )

        return [
            [
                1.0,
                0.0,
            ]
            for _ in texts
        ]
    
    @property
    def model_name(self) -> str:
        return "test-embedder"


def test_indexing_service_processes_documents_in_batches() -> None:
    evidence_repository = InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id=f"document-{index}",
                title=f"Document {index}",
                content="Evidence content.",
                source="Reference",
                source_type=("reviewed_evidence"),
            )
            for index in range(5)
        ]
    )

    embedder = RecordingEmbedder()
    vector_repository = InMemoryVectorRepository()

    service = SemanticIndexingService(
        evidence_repository=(evidence_repository),
        embedder=cast(
            Embedder,
            embedder,
        ),
        vector_repository=(vector_repository),
        batch_size=2,
    )

    result = service.rebuild_index()

    assert result.indexed_documents == 5
    assert [len(batch) for batch in embedder.batches] == [
        2,
        2,
        1,
    ]


def test_indexing_service_rejects_invalid_batch_size() -> None:
    with pytest.raises(
        ValueError,
        match="batch_size",
    ):
        SemanticIndexingService(
            evidence_repository=(create_evidence_repository()),
            embedder=HashingEmbedder(
                dimensions=32,
            ),
            vector_repository=(InMemoryVectorRepository()),
            batch_size=0,
        )


def create_evidence_repository() -> InMemoryEvidenceRepository:
    return InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="allergy-001",
                title="Seasonal allergies",
                content=("Seasonal allergies can cause sneezing and a runny nose."),
                source="Reference",
                source_type="reviewed_evidence",
                metadata={
                    "keywords": "sneezing, runny nose",
                    "specialty": "allergy",
                },
            ),
            EvidenceDocument(
                document_id="sleep-001",
                title="Sleep hygiene",
                content=("Maintain a consistent sleep schedule."),
                source="Reference",
                source_type="reviewed_evidence",
            ),
        ]
    )


def test_indexing_service_rebuilds_index() -> None:
    vector_repository = InMemoryVectorRepository()
    service = SemanticIndexingService(
        evidence_repository=(create_evidence_repository()),
        embedder=HashingEmbedder(
            dimensions=32,
        ),
        vector_repository=vector_repository,
    )

    result = service.rebuild_index()

    assert result.total_documents == 2
    assert result.indexed_documents == 2
    assert result.skipped_documents == 0
    assert vector_repository.count() == 2


def test_indexing_service_replaces_existing_index() -> None:
    vector_repository = InMemoryVectorRepository()
    service = SemanticIndexingService(
        evidence_repository=(create_evidence_repository()),
        embedder=HashingEmbedder(
            dimensions=32,
        ),
        vector_repository=vector_repository,
    )

    service.rebuild_index()
    service.rebuild_index()

    assert vector_repository.count() == 2


def test_indexing_service_indexes_single_document() -> None:
    vector_repository = InMemoryVectorRepository()
    service = SemanticIndexingService(
        evidence_repository=(create_evidence_repository()),
        embedder=HashingEmbedder(
            dimensions=32,
        ),
        vector_repository=vector_repository,
    )

    indexed = service.index_document(
        EvidenceDocument(
            document_id="headache-001",
            title="Headache causes",
            content=("Stress may contribute to headaches."),
            source="Reference",
            source_type="reviewed_evidence",
        )
    )

    assert indexed is True
    assert vector_repository.count() == 1


def test_indexing_service_removes_document() -> None:
    vector_repository = InMemoryVectorRepository()
    service = SemanticIndexingService(
        evidence_repository=(create_evidence_repository()),
        embedder=HashingEmbedder(
            dimensions=32,
        ),
        vector_repository=vector_repository,
    )

    service.rebuild_index()

    removed = service.remove_document(
        "allergy-001",
    )

    assert removed is True
    assert vector_repository.count() == 1
