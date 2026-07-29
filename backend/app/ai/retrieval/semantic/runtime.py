from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from threading import Lock
from time import perf_counter

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
from app.core.metrics import RetrievalMetrics


@dataclass
class SemanticRuntime:
    embedder: Embedder
    vector_repository: VectorRepository
    retrieval_service: SemanticRetrievalService
    indexing_service: SemanticIndexingService
    metrics: RetrievalMetrics = field(
        default_factory=RetrievalMetrics,
    )
    indexing_result: SemanticIndexingResult | None = None
    is_available: bool = False
    startup_error: str | None = None
    recovery_cooldown_seconds: float = 60.0
    last_failure_at: datetime | None = None
    last_recovery_attempt_at: datetime | None = None

    _recovery_lock: Lock = field(
        default_factory=Lock,
        init=False,
        repr=False,
    )

    def synchronize_index(
        self,
    ) -> SemanticIndexingResult:
        started_at = perf_counter()

        try:
            indexing_result = self.indexing_service.rebuild_index()
        except Exception as error:
            self.metrics.record_index_synchronization(
                duration_seconds=(perf_counter() - started_at),
                succeeded=False,
            )

            self.mark_unavailable(
                error,
            )
            raise

        self.metrics.record_index_synchronization(
            duration_seconds=(perf_counter() - started_at),
            succeeded=True,
        )

        self.mark_available(
            indexing_result,
        )

        return indexing_result

    def mark_available(
        self,
        indexing_result: SemanticIndexingResult,
    ) -> None:
        self.indexing_result = indexing_result
        self.is_available = True
        self.startup_error = None
        self.last_failure_at = None

    def mark_unavailable(
        self,
        error: Exception | str,
    ) -> None:
        self.is_available = False
        self.indexing_result = None
        self.startup_error = str(error)
        self.last_failure_at = datetime.now(
            UTC,
        )

    def should_attempt_recovery(
        self,
        *,
        now: datetime | None = None,
    ) -> bool:
        if self.is_available:
            return False

        if self.last_failure_at is None:
            return True

        current_time = now or datetime.now(
            UTC,
        )

        cooldown = timedelta(
            seconds=self.recovery_cooldown_seconds,
        )

        return current_time >= (self.last_failure_at + cooldown)

    def attempt_recovery(
        self,
    ) -> bool:
        if not self.should_attempt_recovery():
            return False

        acquired = self._recovery_lock.acquire(
            blocking=False,
        )

        if not acquired:
            return False

        try:
            if not self.should_attempt_recovery():
                return False

            self.metrics.record_recovery_attempt()

            self.last_recovery_attempt_at = datetime.now(
                UTC,
            )

            try:
                self.synchronize_index()
            except Exception:
                self.metrics.record_recovery_failure()
                return False

            if not self.is_available:
                self.metrics.record_recovery_failure()
                return False

            self.metrics.record_recovery_success()

            return True
        finally:
            self._recovery_lock.release()


def build_semantic_runtime(
    evidence_repository: EvidenceRepository,
    *,
    embedder: Embedder,
    vector_repository: VectorRepository,
    batch_size: int = 100,
    recovery_cooldown_seconds: float = 60.0,
    metrics: RetrievalMetrics | None = None,
) -> SemanticRuntime:
    indexing_service = SemanticIndexingService(
        evidence_repository=evidence_repository,
        embedder=embedder,
        vector_repository=vector_repository,
        batch_size=batch_size,
    )

    retrieval_service = SemanticRetrievalService(
        embedder=embedder,
        repository=vector_repository,
    )

    return SemanticRuntime(
        embedder=embedder,
        vector_repository=vector_repository,
        retrieval_service=retrieval_service,
        indexing_service=indexing_service,
        metrics=metrics or RetrievalMetrics(),
        recovery_cooldown_seconds=(recovery_cooldown_seconds),
    )
