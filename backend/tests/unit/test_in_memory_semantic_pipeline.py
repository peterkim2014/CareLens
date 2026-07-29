from app.ai.retrieval import (
    EvidenceDocument,
    InMemoryEvidenceRepository,
)
from app.ai.retrieval.semantic import (
    HashingEmbedder,
    InMemoryVectorRepository,
    SemanticIndexingService,
    SemanticRetrievalService,
)


def test_in_memory_semantic_pipeline() -> None:
    evidence_repository = InMemoryEvidenceRepository(
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

    embedder = HashingEmbedder(
        dimensions=64,
    )
    vector_repository = InMemoryVectorRepository()

    indexing_service = SemanticIndexingService(
        evidence_repository=evidence_repository,
        embedder=embedder,
        vector_repository=vector_repository,
    )
    retrieval_service = SemanticRetrievalService(
        embedder=embedder,
        repository=vector_repository,
    )

    indexing_result = indexing_service.rebuild_index()
    results = retrieval_service.retrieve(
        "seasonal allergies sneezing",
        limit=1,
    )

    assert indexing_result.indexed_documents == 2
    assert len(results) == 1
    assert results[0].document_id == "allergy-001"
