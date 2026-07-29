from dataclasses import dataclass

from app.ai.retrieval.repository_protocol import (
    EvidenceRepository,
)
from app.ai.retrieval.semantic.embedder_protocol import (
    Embedder,
)
from app.ai.retrieval.semantic.indexing import (
    SemanticIndexingService,
)
from app.ai.retrieval.semantic.repository_protocol import (
    VectorRepository,
)
from app.ai.retrieval.semantic.schemas import (
    SemanticIndexingResult,
)
from app.ai.retrieval.semantic.service import (
    SemanticRetrievalService,
)


@dataclass(frozen=True)
class SemanticRuntime:
    embedder: Embedder
    vector_repository: VectorRepository
    retrieval_service: SemanticRetrievalService
    indexing_service: SemanticIndexingService
    indexing_result: SemanticIndexingResult


def build_semantic_runtime(
    evidence_repository: EvidenceRepository,
    *,
    embedder: Embedder,
    vector_repository: VectorRepository,
    batch_size: int = 100,
) -> SemanticRuntime:
    indexing_service = SemanticIndexingService(
        evidence_repository=evidence_repository,
        embedder=embedder,
        vector_repository=vector_repository,
        batch_size=batch_size,
    )

    indexing_result = indexing_service.rebuild_index()

    retrieval_service = SemanticRetrievalService(
        embedder=embedder,
        repository=vector_repository,
    )

    return SemanticRuntime(
        embedder=embedder,
        vector_repository=vector_repository,
        retrieval_service=retrieval_service,
        indexing_service=indexing_service,
        indexing_result=indexing_result,
    )
