from concurrent.futures import ThreadPoolExecutor

from app.core.metrics import RetrievalMetrics


def test_metrics_start_at_zero() -> None:
    metrics = RetrievalMetrics()

    snapshot = metrics.snapshot()

    assert snapshot.total_requests == 0
    assert snapshot.semantic_attempts == 0
    assert snapshot.semantic_successes == 0
    assert snapshot.semantic_failures == 0
    assert snapshot.lexical_fallbacks == 0
    assert snapshot.recovery_attempts == 0
    assert snapshot.recovery_successes == 0
    assert snapshot.recovery_failures == 0
    assert snapshot.index_synchronizations == 0
    assert snapshot.index_synchronization_successes == 0
    assert snapshot.index_synchronization_failures == 0
    assert snapshot.latest_indexing_duration_seconds is None
    assert snapshot.total_indexing_duration_seconds == 0.0


def test_metrics_record_retrieval_activity() -> None:
    metrics = RetrievalMetrics()

    metrics.record_request()
    metrics.record_semantic_attempt()
    metrics.record_semantic_success()

    snapshot = metrics.snapshot()

    assert snapshot.total_requests == 1
    assert snapshot.semantic_attempts == 1
    assert snapshot.semantic_successes == 1
    assert snapshot.semantic_failures == 0
    assert snapshot.lexical_fallbacks == 0


def test_metrics_record_semantic_fallback() -> None:
    metrics = RetrievalMetrics()

    metrics.record_request()
    metrics.record_semantic_attempt()
    metrics.record_semantic_failure()
    metrics.record_lexical_fallback()

    snapshot = metrics.snapshot()

    assert snapshot.total_requests == 1
    assert snapshot.semantic_attempts == 1
    assert snapshot.semantic_successes == 0
    assert snapshot.semantic_failures == 1
    assert snapshot.lexical_fallbacks == 1


def test_metrics_record_index_synchronization() -> None:
    metrics = RetrievalMetrics()

    metrics.record_index_synchronization(
        duration_seconds=0.25,
        succeeded=True,
    )

    metrics.record_index_synchronization(
        duration_seconds=0.75,
        succeeded=False,
    )

    snapshot = metrics.snapshot()

    assert snapshot.index_synchronizations == 2
    assert snapshot.index_synchronization_successes == 1
    assert snapshot.index_synchronization_failures == 1
    assert snapshot.latest_indexing_duration_seconds == 0.75
    assert snapshot.total_indexing_duration_seconds == 1.0


def test_metrics_are_thread_safe() -> None:
    metrics = RetrievalMetrics()

    def record_requests() -> None:
        for _ in range(1_000):
            metrics.record_request()

    with ThreadPoolExecutor(
        max_workers=8,
    ) as executor:
        futures = [
            executor.submit(
                record_requests,
            )
            for _ in range(8)
        ]

        for future in futures:
            future.result()

    assert metrics.snapshot().total_requests == 8_000
