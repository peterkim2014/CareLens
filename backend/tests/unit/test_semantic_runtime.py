from app.ai.retrieval import (
    EvidenceDocument,
    InMemoryEvidenceRepository,
)
from app.ai.retrieval.semantic import (
    HashingEmbedder,
    SemanticRuntime,
    build_semantic_runtime,
)
from app.ai.retrieval.semantic.in_memory_repository import (
    InMemoryVectorRepository,
)


def create_evidence_repository() -> InMemoryEvidenceRepository:
    return InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="allergy-001",
                title="Seasonal allergies",
                content=("Seasonal allergies may cause sneezing and itchy eyes."),
                source="Reference",
                source_type="reviewed_evidence",
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


def test_build_semantic_runtime_indexes_documents() -> None:
    evidence_repository = create_evidence_repository()
    embedder = HashingEmbedder(
        dimensions=32,
    )

    runtime = build_semantic_runtime(
        evidence_repository,
        embedder=embedder,
        vector_repository=InMemoryVectorRepository(),
    )

    assert isinstance(
        runtime,
        SemanticRuntime,
    )
    assert runtime.embedder is embedder
    assert embedder.dimensions == 32
    assert runtime.indexing_result.total_documents == 2
    assert runtime.indexing_result.indexed_documents == 2
    assert runtime.indexing_result.skipped_documents == 0
    assert runtime.vector_repository.count() == 2


def test_semantic_runtime_can_retrieve_indexed_document() -> None:
    evidence_repository = create_evidence_repository()
    embedder = HashingEmbedder(
        dimensions=64,
    )

    runtime = build_semantic_runtime(
        evidence_repository,
        embedder=embedder,
        vector_repository=InMemoryVectorRepository(),
    )

    results = runtime.retrieval_service.retrieve(
        "seasonal allergies sneezing",
        limit=1,
    )

    assert len(results) == 1
    assert results[0].document_id == "allergy-001"
