from app.ai.retrieval import (
    EvidenceDocument,
    InMemoryEvidenceRepository,
    RetrievalService,
)
from app.ai.retrieval.semantic.schemas import (
    SemanticSearchResult,
)
from app.core.metrics import RetrievalMetrics


class FailingSemanticRetriever:
    def __init__(
        self,
        error: Exception,
    ) -> None:
        self._error = error
        self.received_query: str | None = None
        self.received_limit: int | None = None

    def retrieve(
        self,
        query: str,
        *,
        limit: int,
    ) -> list[SemanticSearchResult]:
        self.received_query = query
        self.received_limit = limit

        raise self._error


class FakeSemanticRetriever:
    def __init__(
        self,
        results: list[SemanticSearchResult],
    ) -> None:
        self._results = results
        self.received_query: str | None = None
        self.received_limit: int | None = None

    def retrieve(
        self,
        query: str,
        *,
        limit: int,
    ) -> list[SemanticSearchResult]:
        self.received_query = query
        self.received_limit = limit

        return self._results[:limit]


def create_service() -> RetrievalService:
    repository = InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="allergy-001",
                title="Seasonal allergy symptoms",
                content=(
                    "Seasonal allergies may cause sneezing, "
                    "itchy eyes, congestion, and a runny nose."
                ),
                source="Clinical Reference",
                source_type="clinical_reference",
            ),
            EvidenceDocument(
                document_id="sleep-001",
                title="Sleep hygiene",
                content=("Consistent sleep schedules can improve sleep quality."),
                source="Clinical Reference",
                source_type="clinical_reference",
            ),
        ]
    )

    return RetrievalService(
        repository=repository,
        minimum_score=0.1,
        maximum_results=5,
    )


def test_retrieval_records_lexical_request() -> None:
    metrics = RetrievalMetrics()

    repository = InMemoryEvidenceRepository(
        documents=[],
    )

    service = RetrievalService(
        repository=repository,
        metrics=metrics,
    )

    service.retrieve(
        "allergy symptoms",
    )

    snapshot = metrics.snapshot()

    assert snapshot.total_requests == 1
    assert snapshot.semantic_attempts == 0
    assert snapshot.semantic_successes == 0
    assert snapshot.semantic_failures == 0
    assert snapshot.lexical_fallbacks == 0


def test_retrieval_records_semantic_success() -> None:
    metrics = RetrievalMetrics()

    repository = InMemoryEvidenceRepository(
        documents=[],
    )

    semantic_retriever = FakeSemanticRetriever(
        results=[],
    )

    service = RetrievalService(
        repository=repository,
        semantic_retriever=semantic_retriever,
        metrics=metrics,
    )

    service.retrieve(
        "allergy symptoms",
    )

    snapshot = metrics.snapshot()

    assert snapshot.total_requests == 1
    assert snapshot.semantic_attempts == 1
    assert snapshot.semantic_successes == 1
    assert snapshot.semantic_failures == 0
    assert snapshot.lexical_fallbacks == 0


def test_retrieval_records_semantic_failure_and_fallback() -> None:
    metrics = RetrievalMetrics()

    repository = InMemoryEvidenceRepository(
        documents=[],
    )

    service = RetrievalService(
        repository=repository,
        semantic_retriever=(
            FailingSemanticRetriever(
                RuntimeError(
                    "provider unavailable",
                )
            )
        ),
        metrics=metrics,
    )

    service.retrieve(
        "allergy symptoms",
    )

    snapshot = metrics.snapshot()

    assert snapshot.total_requests == 1
    assert snapshot.semantic_attempts == 1
    assert snapshot.semantic_successes == 0
    assert snapshot.semantic_failures == 1
    assert snapshot.lexical_fallbacks == 1


def test_semantic_failure_falls_back_to_lexical_retrieval() -> None:
    repository = InMemoryEvidenceRepository(
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

    semantic_retriever = FailingSemanticRetriever(
        RuntimeError(
            "provider unavailable",
        )
    )

    service = RetrievalService(
        repository=repository,
        semantic_retriever=semantic_retriever,
    )

    result = service.retrieve(
        "seasonal allergies sneezing",
    )

    assert result.total_candidates == 2
    assert len(result.evidence) == 1
    assert result.evidence[0].document_id == ("allergy-001")
    assert "seasonal" in (result.evidence[0].matched_terms)
    assert semantic_retriever.received_query == ("seasonal allergies sneezing")
    assert semantic_retriever.received_limit == 5


def test_semantic_failure_calls_failure_handler() -> None:
    repository = InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="allergy-001",
                title="Seasonal allergies",
                content=("Seasonal allergies may cause sneezing."),
                source="Reference",
                source_type="reviewed_evidence",
            ),
        ]
    )

    semantic_error = RuntimeError(
        "database unavailable",
    )

    received_errors: list[Exception] = []

    service = RetrievalService(
        repository=repository,
        semantic_retriever=(
            FailingSemanticRetriever(
                semantic_error,
            )
        ),
        semantic_failure_handler=(received_errors.append),
    )

    result = service.retrieve(
        "seasonal allergies",
    )

    assert len(result.evidence) == 1
    assert received_errors == [
        semantic_error,
    ]


def test_failure_handler_error_does_not_break_lexical_fallback() -> None:
    repository = InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="allergy-001",
                title="Seasonal allergies",
                content=("Seasonal allergies may cause sneezing."),
                source="Reference",
                source_type="reviewed_evidence",
            ),
        ]
    )

    def fail_handler(
        _: Exception,
    ) -> None:
        raise RuntimeError(
            "handler failed",
        )

    service = RetrievalService(
        repository=repository,
        semantic_retriever=(
            FailingSemanticRetriever(
                RuntimeError(
                    "semantic failure",
                )
            )
        ),
        semantic_failure_handler=fail_handler,
    )

    result = service.retrieve(
        "seasonal allergies",
    )

    assert len(result.evidence) == 1
    assert result.evidence[0].document_id == ("allergy-001")


def test_hybrid_retrieval_includes_semantic_match() -> None:
    repository = InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="allergy-001",
                title="Seasonal allergy symptoms",
                content=("Seasonal allergies can cause a runny nose."),
                source="Reference",
                source_type="reviewed_evidence",
            ),
            EvidenceDocument(
                document_id="sleep-001",
                title="Sleep hygiene",
                content=("Maintain a consistent schedule."),
                source="Reference",
                source_type="reviewed_evidence",
            ),
        ]
    )

    semantic_retriever = FakeSemanticRetriever(
        results=[
            SemanticSearchResult(
                document_id="allergy-001",
                similarity=0.95,
            ),
        ],
    )

    service = RetrievalService(
        repository=repository,
        semantic_retriever=semantic_retriever,
    )

    result = service.retrieve(
        "my nose keeps dripping",
    )

    assert len(result.evidence) == 1
    assert result.evidence[0].document_id == ("allergy-001")
    assert result.evidence[0].matched_terms == [
        "nose",
    ]

    assert semantic_retriever.received_query == ("my nose keeps dripping")
    assert semantic_retriever.received_limit == 5


def test_hybrid_retrieval_rewards_shared_match() -> None:
    repository = InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="allergy-001",
                title="Seasonal allergy symptoms",
                content=("Allergies can cause sneezing and itchy eyes."),
                source="Reference",
                source_type="reviewed_evidence",
            ),
            EvidenceDocument(
                document_id="sleep-001",
                title="Sleep hygiene",
                content=("Maintain a sleep schedule."),
                source="Reference",
                source_type="reviewed_evidence",
            ),
        ]
    )

    semantic_retriever = FakeSemanticRetriever(
        results=[
            SemanticSearchResult(
                document_id="allergy-001",
                similarity=0.95,
            ),
            SemanticSearchResult(
                document_id="sleep-001",
                similarity=0.80,
            ),
        ],
    )

    service = RetrievalService(
        repository=repository,
        semantic_retriever=semantic_retriever,
    )

    result = service.retrieve(
        "seasonal allergies",
    )

    assert result.evidence[0].document_id == ("allergy-001")
    assert result.evidence[0].score > result.evidence[1].score


def test_hybrid_retrieval_excludes_unknown_document() -> None:
    repository = InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="allergy-001",
                title="Allergies",
                content="Allergy guidance.",
                source="Reference",
                source_type="reviewed_evidence",
            ),
        ]
    )

    semantic_retriever = FakeSemanticRetriever(
        results=[
            SemanticSearchResult(
                document_id="missing-001",
                similarity=0.99,
            ),
        ],
    )

    service = RetrievalService(
        repository=repository,
        semantic_retriever=semantic_retriever,
    )

    result = service.retrieve(
        "unrecognized semantic phrase",
    )

    assert result.total_candidates == 1
    assert result.evidence == []


def test_retrieval_returns_matching_evidence() -> None:
    result = create_service().retrieve(
        "What symptoms do seasonal allergies cause?",
    )

    assert result.total_candidates == 2
    assert len(result.evidence) == 1
    assert result.evidence[0].document_id == ("allergy-001")
    assert result.evidence[0].score > 0.0
    assert "seasonal" in (result.evidence[0].matched_terms)


def test_retrieval_excludes_irrelevant_documents() -> None:
    result = create_service().retrieve(
        "What causes kidney stones?",
    )

    assert result.evidence == []


def test_retrieval_excludes_stopword_only_matches() -> None:
    repository = InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="headache-001",
                title="Common headache causes",
                content=("Stress and insufficient sleep can contribute to headaches."),
                source="Clinical Reference",
                source_type="clinical_reference",
            ),
        ]
    )

    service = RetrievalService(
        repository=repository,
        minimum_score=0.1,
    )

    result = service.retrieve(
        "I have sneezing and itchy eyes.",
    )

    assert result.total_candidates == 1
    assert result.evidence == []


def test_retrieval_does_not_return_stopwords_as_matches() -> None:
    result = create_service().retrieve(
        "I have sneezing and itchy eyes.",
    )

    assert len(result.evidence) == 1

    matched_terms = result.evidence[0].matched_terms

    assert "sneezing" in matched_terms
    assert "itchy" in matched_terms
    assert "eyes" in matched_terms

    assert "i" not in matched_terms
    assert "have" not in matched_terms
    assert "and" not in matched_terms


def test_retrieval_handles_punctuation_and_case() -> None:
    result = create_service().retrieve(
        "SNEEZING, ITCHY EYES!",
    )

    assert len(result.evidence) == 1
    assert result.evidence[0].document_id == ("allergy-001")
    assert result.evidence[0].matched_terms == [
        "eyes",
        "itchy",
        "sneezing",
    ]


def test_retrieval_returns_no_evidence_for_stopword_query() -> None:
    result = create_service().retrieve(
        "What is it and how does it work?",
    )

    assert result.total_candidates == 2
    assert result.evidence == []


def test_retrieval_orders_results_by_score() -> None:
    repository = InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="partial",
                title="Allergies",
                content=("Allergies can cause symptoms."),
                source="Reference",
                source_type="clinical_reference",
            ),
            EvidenceDocument(
                document_id="strong",
                title="Seasonal allergy symptoms",
                content=("Seasonal allergies cause sneezing and itchy eyes."),
                source="Reference",
                source_type="clinical_reference",
            ),
        ]
    )

    service = RetrievalService(
        repository=repository,
    )

    result = service.retrieve(
        "seasonal allergy symptoms sneezing itchy eyes",
    )

    assert result.evidence[0].document_id == "strong"


def test_retrieval_limits_result_count() -> None:
    documents = [
        EvidenceDocument(
            document_id=f"document-{index}",
            title="Headache causes",
            content="Stress can cause headaches.",
            source="Reference",
            source_type="clinical_reference",
        )
        for index in range(10)
    ]

    service = RetrievalService(
        repository=InMemoryEvidenceRepository(
            documents,
        ),
        maximum_results=3,
    )

    result = service.retrieve(
        "headache stress",
    )

    assert len(result.evidence) == 3


def test_retrieval_uses_keyword_metadata() -> None:
    repository = InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="allergy-001",
                title="Patient education",
                content=("This document provides general patient guidance."),
                source="Reference",
                source_type="reviewed_evidence",
                metadata={
                    "keywords": ("seasonal allergies,sneezing,itchy eyes"),
                },
            ),
        ]
    )

    service = RetrievalService(
        repository=repository,
        minimum_score=0.1,
    )

    result = service.retrieve(
        "seasonal allergies",
    )

    assert len(result.evidence) == 1
    assert result.evidence[0].document_id == ("allergy-001")
    assert result.evidence[0].matched_terms == [
        "allergies",
        "seasonal",
    ]


def test_retrieval_uses_specialty_metadata() -> None:
    repository = InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="cardiology-001",
                title="Clinical overview",
                content="Reviewed clinical information.",
                source="Reference",
                source_type="reviewed_evidence",
                metadata={
                    "specialty": "cardiology",
                },
            ),
        ]
    )

    service = RetrievalService(
        repository=repository,
        minimum_score=0.1,
    )

    result = service.retrieve(
        "cardiology",
    )

    assert len(result.evidence) == 1
    assert result.evidence[0].document_id == ("cardiology-001")
    assert result.evidence[0].matched_terms == [
        "cardiology",
    ]


def test_title_match_ranks_above_content_match() -> None:
    repository = InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="content-match",
                title="Clinical overview",
                content=("Seasonal allergies are discussed in this evidence."),
                source="Reference",
                source_type="reviewed_evidence",
            ),
            EvidenceDocument(
                document_id="title-match",
                title="Seasonal allergies",
                content="Reviewed clinical evidence.",
                source="Reference",
                source_type="reviewed_evidence",
            ),
        ]
    )

    service = RetrievalService(
        repository=repository,
        minimum_score=0.1,
    )

    result = service.retrieve(
        "seasonal allergies",
    )

    assert len(result.evidence) == 2
    assert result.evidence[0].document_id == ("title-match")
    assert result.evidence[0].score > result.evidence[1].score


def test_keyword_match_ranks_above_content_match() -> None:
    repository = InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="content-match",
                title="Patient information",
                content=("Sneezing may occur in some conditions."),
                source="Reference",
                source_type="reviewed_evidence",
            ),
            EvidenceDocument(
                document_id="keyword-match",
                title="Clinical evidence",
                content="Reviewed information.",
                source="Reference",
                source_type="reviewed_evidence",
                metadata={
                    "keywords": "sneezing",
                },
            ),
        ]
    )

    service = RetrievalService(
        repository=repository,
        minimum_score=0.1,
    )

    result = service.retrieve(
        "sneezing",
    )

    assert len(result.evidence) == 2
    assert result.evidence[0].document_id == ("keyword-match")


def test_equal_scores_order_by_document_id() -> None:
    repository = InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="document-b",
                title="Headache",
                content="Clinical evidence.",
                source="Reference",
                source_type="reviewed_evidence",
            ),
            EvidenceDocument(
                document_id="document-a",
                title="Headache",
                content="Clinical evidence.",
                source="Reference",
                source_type="reviewed_evidence",
            ),
        ]
    )

    service = RetrievalService(
        repository=repository,
        minimum_score=0.1,
    )

    result = service.retrieve(
        "headache",
    )

    assert [item.document_id for item in result.evidence] == [
        "document-a",
        "document-b",
    ]
