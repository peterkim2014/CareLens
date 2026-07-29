import logging
from collections.abc import Callable

from app.ai.retrieval.fusion import (
    reciprocal_rank_fusion,
)
from app.ai.retrieval.repository_protocol import (
    EvidenceRepository,
)
from app.ai.retrieval.schemas import (
    EvidenceDocument,
    RetrievalResult,
    RetrievedEvidence,
)
from app.ai.retrieval.scoring import (
    CONTENT_WEIGHT,
    KEYWORD_WEIGHT,
    SPECIALTY_WEIGHT,
    TITLE_WEIGHT,
    WeightedTextField,
    weighted_lexical_score,
)
from app.ai.retrieval.semantic.protocol import (
    SemanticRetriever,
)
from app.core.metrics import RetrievalMetrics

logger = logging.getLogger(__name__)

SemanticFailureHandler = Callable[
    [Exception],
    None,
]


class RetrievalService:
    def __init__(
        self,
        repository: EvidenceRepository,
        minimum_score: float = 0.1,
        maximum_results: int = 5,
        semantic_retriever: SemanticRetriever | None = None,
        lexical_weight: float = 1.0,
        semantic_weight: float = 1.0,
        semantic_failure_handler: (SemanticFailureHandler | None) = None,
        metrics: RetrievalMetrics | None = None,
    ) -> None:
        if not 0.0 <= minimum_score <= 1.0:
            raise ValueError(
                "minimum_score must be between 0.0 and 1.0.",
            )

        if maximum_results < 1:
            raise ValueError(
                "maximum_results must be at least 1.",
            )

        if lexical_weight < 0.0:
            raise ValueError(
                "lexical_weight cannot be negative.",
            )

        if semantic_weight < 0.0:
            raise ValueError(
                "semantic_weight cannot be negative.",
            )

        if lexical_weight == 0.0 and semantic_weight == 0.0:
            raise ValueError(
                "At least one retrieval weight must be positive.",
            )

        self._repository = repository
        self._minimum_score = minimum_score
        self._maximum_results = maximum_results
        self._semantic_retriever = semantic_retriever
        self._lexical_weight = lexical_weight
        self._semantic_weight = semantic_weight
        self._semantic_failure_handler = semantic_failure_handler
        self._metrics = metrics or RetrievalMetrics()

    def retrieve(
        self,
        query: str,
    ) -> RetrievalResult:
        self._metrics.record_request()

        documents = self._repository.list_documents()

        lexical_evidence = self._retrieve_lexically(
            query=query,
            documents=documents,
        )

        if self._semantic_retriever is None:
            return self._build_lexical_result(
                query=query,
                documents=documents,
                lexical_evidence=lexical_evidence,
            )

        self._metrics.record_semantic_attempt()

        try:
            result = self._retrieve_hybrid(
                query=query,
                documents=documents,
                lexical_evidence=lexical_evidence,
            )
        except Exception as error:
            self._metrics.record_semantic_failure()
            self._metrics.record_lexical_fallback()

            self._handle_semantic_failure(
                error,
            )

            return self._build_lexical_result(
                query=query,
                documents=documents,
                lexical_evidence=lexical_evidence,
            )

        self._metrics.record_semantic_success()

        return result

    def _retrieve_lexically(
        self,
        *,
        query: str,
        documents: list[EvidenceDocument],
    ) -> list[RetrievedEvidence]:
        evidence: list[RetrievedEvidence] = []

        for document in documents:
            score, matched_terms = weighted_lexical_score(
                query,
                fields=(
                    WeightedTextField(
                        text=document.title,
                        weight=TITLE_WEIGHT,
                    ),
                    WeightedTextField(
                        text=document.metadata.get(
                            "keywords",
                            "",
                        ),
                        weight=KEYWORD_WEIGHT,
                    ),
                    WeightedTextField(
                        text=document.metadata.get(
                            "specialty",
                            "",
                        ),
                        weight=SPECIALTY_WEIGHT,
                    ),
                    WeightedTextField(
                        text=document.content,
                        weight=CONTENT_WEIGHT,
                    ),
                ),
            )

            if score < self._minimum_score:
                continue

            evidence.append(
                self._to_retrieved_evidence(
                    document=document,
                    score=score,
                    matched_terms=matched_terms,
                )
            )

        evidence.sort(
            key=lambda item: (
                -item.score,
                item.document_id,
            ),
        )

        return evidence

    def _retrieve_hybrid(
        self,
        *,
        query: str,
        documents: list[EvidenceDocument],
        lexical_evidence: list[RetrievedEvidence],
    ) -> RetrievalResult:
        if self._semantic_retriever is None:
            raise RuntimeError(
                "Semantic retriever is not configured.",
            )

        semantic_results = self._semantic_retriever.retrieve(
            query,
            limit=self._maximum_results,
        )

        documents_by_id = {document.document_id: document for document in documents}

        lexical_by_id = {item.document_id: item for item in lexical_evidence}

        valid_semantic_results = [
            result
            for result in semantic_results
            if result.document_id in documents_by_id
        ]

        fused_results = reciprocal_rank_fusion(
            lexical_ranking=[item.document_id for item in lexical_evidence],
            semantic_ranking=[item.document_id for item in valid_semantic_results],
            lexical_weight=self._lexical_weight,
            semantic_weight=self._semantic_weight,
        )

        evidence: list[RetrievedEvidence] = []

        for fused_result in fused_results[: self._maximum_results]:
            lexical_item = lexical_by_id.get(
                fused_result.document_id,
            )

            if lexical_item is not None:
                matched_terms = lexical_item.matched_terms
            else:
                matched_terms = []

            document = documents_by_id[fused_result.document_id]

            evidence.append(
                self._to_retrieved_evidence(
                    document=document,
                    score=fused_result.score,
                    matched_terms=matched_terms,
                )
            )

        return RetrievalResult(
            query=query,
            total_candidates=len(documents),
            evidence=evidence,
        )

    def _handle_semantic_failure(
        self,
        error: Exception,
    ) -> None:
        logger.exception(
            "Semantic retrieval failed; falling back to lexical retrieval",
            extra={
                "event": "semantic_retrieval_failed",
                "error_type": type(
                    error,
                ).__name__,
            },
        )

        if self._semantic_failure_handler is None:
            return

        try:
            self._semantic_failure_handler(
                error,
            )
        except Exception:
            logger.exception(
                "Semantic failure handler failed",
                extra={
                    "event": ("semantic_failure_handler_failed"),
                },
            )

    def _build_lexical_result(
        self,
        *,
        query: str,
        documents: list[EvidenceDocument],
        lexical_evidence: list[RetrievedEvidence],
    ) -> RetrievalResult:
        return RetrievalResult(
            query=query,
            total_candidates=len(documents),
            evidence=lexical_evidence[: self._maximum_results],
        )

    @staticmethod
    def _to_retrieved_evidence(
        *,
        document: EvidenceDocument,
        score: float,
        matched_terms: list[str],
    ) -> RetrievedEvidence:
        return RetrievedEvidence(
            document_id=document.document_id,
            title=document.title,
            content=document.content,
            source=document.source,
            source_type=document.source_type,
            score=score,
            matched_terms=matched_terms,
            metadata=document.metadata,
        )
