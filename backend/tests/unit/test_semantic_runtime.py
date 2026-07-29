from datetime import timedelta

import pytest

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
from app.ai.retrieval.semantic.schemas import (
    SemanticIndexingResult,
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


def create_runtime(
    *,
    recovery_cooldown_seconds: float = 60.0,
) -> SemanticRuntime:
    return build_semantic_runtime(
        create_evidence_repository(),
        embedder=HashingEmbedder(
            dimensions=32,
        ),
        vector_repository=(InMemoryVectorRepository()),
        recovery_cooldown_seconds=(recovery_cooldown_seconds),
    )


def test_unavailable_runtime_waits_for_recovery_cooldown() -> None:
    runtime = create_runtime(
        recovery_cooldown_seconds=60.0,
    )

    runtime.mark_unavailable(
        RuntimeError(
            "provider unavailable",
        )
    )

    assert runtime.last_failure_at is not None

    now = runtime.last_failure_at + timedelta(
        seconds=30,
    )

    assert (
        runtime.should_attempt_recovery(
            now=now,
        )
        is False
    )


def test_unavailable_runtime_allows_recovery_after_cooldown() -> None:
    runtime = create_runtime(
        recovery_cooldown_seconds=60.0,
    )

    runtime.mark_unavailable(
        RuntimeError(
            "provider unavailable",
        )
    )

    assert runtime.last_failure_at is not None

    now = runtime.last_failure_at + timedelta(
        seconds=60,
    )

    assert (
        runtime.should_attempt_recovery(
            now=now,
        )
        is True
    )


def test_available_runtime_does_not_attempt_recovery() -> None:
    runtime = create_runtime(
        recovery_cooldown_seconds=0.0,
    )

    runtime.synchronize_index()

    assert runtime.is_available is True
    assert runtime.should_attempt_recovery() is False


def test_attempt_recovery_restores_runtime() -> None:
    runtime = create_runtime(
        recovery_cooldown_seconds=0.0,
    )

    runtime.mark_unavailable(
        RuntimeError(
            "temporary failure",
        )
    )

    recovered = runtime.attempt_recovery()

    snapshot = runtime.metrics.snapshot()

    assert recovered is True
    assert runtime.is_available is True
    assert runtime.startup_error is None
    assert runtime.last_recovery_attempt_at is not None
    assert snapshot.recovery_attempts == 1
    assert snapshot.recovery_successes == 1
    assert snapshot.recovery_failures == 0
    assert snapshot.index_synchronizations == 1
    assert snapshot.index_synchronization_successes == 1
    assert snapshot.index_synchronization_failures == 0


def test_failed_recovery_keeps_runtime_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = create_runtime(
        recovery_cooldown_seconds=0.0,
    )

    runtime.mark_unavailable(
        RuntimeError(
            "temporary failure",
        )
    )

    def fail_rebuild() -> SemanticIndexingResult:
        raise RuntimeError(
            "still unavailable",
        )

    monkeypatch.setattr(
        runtime.indexing_service,
        "rebuild_index",
        fail_rebuild,
    )

    recovered = runtime.attempt_recovery()

    snapshot = runtime.metrics.snapshot()

    assert recovered is False
    assert runtime.is_available is False
    assert runtime.startup_error == ("still unavailable")
    assert snapshot.recovery_attempts == 1
    assert snapshot.recovery_successes == 0
    assert snapshot.recovery_failures == 1
    assert snapshot.index_synchronizations == 1
    assert snapshot.index_synchronization_successes == 0
    assert snapshot.index_synchronization_failures == 1


def test_build_semantic_runtime_does_not_index_immediately() -> None:
    runtime = create_runtime()

    snapshot = runtime.metrics.snapshot()

    assert isinstance(
        runtime,
        SemanticRuntime,
    )
    assert runtime.is_available is False
    assert runtime.indexing_result is None
    assert runtime.startup_error is None
    assert runtime.vector_repository.count() == 0
    assert snapshot.index_synchronizations == 0


def test_semantic_runtime_synchronizes_index() -> None:
    runtime = create_runtime()

    indexing_result = runtime.synchronize_index()

    snapshot = runtime.metrics.snapshot()

    assert runtime.is_available is True
    assert runtime.startup_error is None
    assert runtime.indexing_result is indexing_result
    assert indexing_result.total_documents == 2
    assert indexing_result.indexed_documents == 2
    assert indexing_result.skipped_documents == 0
    assert runtime.vector_repository.count() == 2

    assert snapshot.index_synchronizations == 1
    assert snapshot.index_synchronization_successes == 1
    assert snapshot.index_synchronization_failures == 0
    assert snapshot.latest_indexing_duration_seconds is not None
    assert snapshot.latest_indexing_duration_seconds >= 0.0
    assert snapshot.total_indexing_duration_seconds >= 0.0


def test_semantic_runtime_can_retrieve_indexed_document() -> None:
    runtime = create_runtime()

    runtime.synchronize_index()

    results = runtime.retrieval_service.retrieve(
        "seasonal allergies sneezing",
        limit=1,
    )

    assert len(results) == 1
    assert results[0].document_id == ("allergy-001")


def test_semantic_runtime_marks_itself_available() -> None:
    runtime = create_runtime()

    indexing_result = runtime.indexing_service.rebuild_index()

    runtime.mark_available(
        indexing_result,
    )

    assert runtime.is_available is True
    assert runtime.indexing_result is indexing_result
    assert runtime.startup_error is None
    assert runtime.last_failure_at is None


def test_semantic_runtime_records_startup_failure() -> None:
    runtime = create_runtime()

    runtime.mark_unavailable(
        RuntimeError(
            "provider unavailable",
        )
    )

    assert runtime.is_available is False
    assert runtime.indexing_result is None
    assert runtime.startup_error == ("provider unavailable")
    assert runtime.last_failure_at is not None


def test_synchronize_index_marks_runtime_unavailable_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = create_runtime()

    def fail_rebuild() -> SemanticIndexingResult:
        raise RuntimeError(
            "index unavailable",
        )

    monkeypatch.setattr(
        runtime.indexing_service,
        "rebuild_index",
        fail_rebuild,
    )

    with pytest.raises(
        RuntimeError,
        match="index unavailable",
    ):
        runtime.synchronize_index()

    snapshot = runtime.metrics.snapshot()

    assert runtime.is_available is False
    assert runtime.indexing_result is None
    assert runtime.startup_error == ("index unavailable")
    assert runtime.last_failure_at is not None
    assert snapshot.index_synchronizations == 1
    assert snapshot.index_synchronization_successes == 0
    assert snapshot.index_synchronization_failures == 1
    assert snapshot.latest_indexing_duration_seconds is not None
