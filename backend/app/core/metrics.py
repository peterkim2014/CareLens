from dataclasses import dataclass
from threading import Lock


@dataclass(
    frozen=True,
    slots=True,
)
class RetrievalMetricsSnapshot:
    total_requests: int
    semantic_attempts: int
    semantic_successes: int
    semantic_failures: int
    lexical_fallbacks: int

    recovery_attempts: int
    recovery_successes: int
    recovery_failures: int

    index_synchronizations: int
    index_synchronization_successes: int
    index_synchronization_failures: int
    latest_indexing_duration_seconds: float | None
    total_indexing_duration_seconds: float


class RetrievalMetrics:
    def __init__(
        self,
    ) -> None:
        self._lock = Lock()

        self._total_requests = 0
        self._semantic_attempts = 0
        self._semantic_successes = 0
        self._semantic_failures = 0
        self._lexical_fallbacks = 0

        self._recovery_attempts = 0
        self._recovery_successes = 0
        self._recovery_failures = 0

        self._index_synchronizations = 0
        self._index_synchronization_successes = 0
        self._index_synchronization_failures = 0
        self._latest_indexing_duration_seconds: float | None = None
        self._total_indexing_duration_seconds = 0.0

    def record_request(
        self,
    ) -> None:
        with self._lock:
            self._total_requests += 1

    def record_semantic_attempt(
        self,
    ) -> None:
        with self._lock:
            self._semantic_attempts += 1

    def record_semantic_success(
        self,
    ) -> None:
        with self._lock:
            self._semantic_successes += 1

    def record_semantic_failure(
        self,
    ) -> None:
        with self._lock:
            self._semantic_failures += 1

    def record_lexical_fallback(
        self,
    ) -> None:
        with self._lock:
            self._lexical_fallbacks += 1

    def record_recovery_attempt(
        self,
    ) -> None:
        with self._lock:
            self._recovery_attempts += 1

    def record_recovery_success(
        self,
    ) -> None:
        with self._lock:
            self._recovery_successes += 1

    def record_recovery_failure(
        self,
    ) -> None:
        with self._lock:
            self._recovery_failures += 1

    def record_index_synchronization(
        self,
        *,
        duration_seconds: float,
        succeeded: bool,
    ) -> None:
        normalized_duration = max(
            duration_seconds,
            0.0,
        )

        with self._lock:
            self._index_synchronizations += 1
            self._latest_indexing_duration_seconds = normalized_duration
            self._total_indexing_duration_seconds += normalized_duration

            if succeeded:
                self._index_synchronization_successes += 1
            else:
                self._index_synchronization_failures += 1

    def snapshot(
        self,
    ) -> RetrievalMetricsSnapshot:
        with self._lock:
            return RetrievalMetricsSnapshot(
                total_requests=self._total_requests,
                semantic_attempts=self._semantic_attempts,
                semantic_successes=self._semantic_successes,
                semantic_failures=self._semantic_failures,
                lexical_fallbacks=self._lexical_fallbacks,
                recovery_attempts=self._recovery_attempts,
                recovery_successes=self._recovery_successes,
                recovery_failures=self._recovery_failures,
                index_synchronizations=(self._index_synchronizations),
                index_synchronization_successes=(self._index_synchronization_successes),
                index_synchronization_failures=(self._index_synchronization_failures),
                latest_indexing_duration_seconds=(
                    self._latest_indexing_duration_seconds
                ),
                total_indexing_duration_seconds=(self._total_indexing_duration_seconds),
            )
