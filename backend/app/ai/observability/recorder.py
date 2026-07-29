from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter_ns

from app.ai.observability.schemas import (
    AuditMetadataValue,
    PipelineAudit,
    PipelineEvent,
    PipelineEventStatus,
)


@dataclass(frozen=True, slots=True)
class StageTimer:
    started_at: datetime
    started_ns: int


class PipelineAuditRecorder:
    def __init__(self) -> None:
        self._started_at = datetime.now(UTC)
        self._started_ns = perf_counter_ns()
        self._events: list[PipelineEvent] = []

    def start_stage(self) -> StageTimer:
        return StageTimer(
            started_at=datetime.now(UTC),
            started_ns=perf_counter_ns(),
        )

    def complete_stage(
        self,
        stage: str,
        timer: StageTimer,
        metadata: dict[str, AuditMetadataValue] | None = None,
    ) -> None:
        completed_at = datetime.now(UTC)
        completed_ns = perf_counter_ns()

        self._events.append(
            PipelineEvent(
                stage=stage,
                status=PipelineEventStatus.COMPLETED,
                started_at=timer.started_at,
                completed_at=completed_at,
                duration_ms=self._duration_ms(
                    start_ns=timer.started_ns,
                    end_ns=completed_ns,
                ),
                metadata=metadata or {},
            )
        )

    def fail_stage(
        self,
        stage: str,
        timer: StageTimer,
        error_type: str,
    ) -> None:
        completed_at = datetime.now(UTC)
        completed_ns = perf_counter_ns()

        self._events.append(
            PipelineEvent(
                stage=stage,
                status=PipelineEventStatus.FAILED,
                started_at=timer.started_at,
                completed_at=completed_at,
                duration_ms=self._duration_ms(
                    start_ns=timer.started_ns,
                    end_ns=completed_ns,
                ),
                metadata={
                    "error_type": error_type,
                },
            )
        )

    def build(self) -> PipelineAudit:
        completed_at = datetime.now(UTC)
        completed_ns = perf_counter_ns()

        return PipelineAudit(
            started_at=self._started_at,
            completed_at=completed_at,
            total_duration_ms=self._duration_ms(
                start_ns=self._started_ns,
                end_ns=completed_ns,
            ),
            events=list(self._events),
        )

    def _duration_ms(
        self,
        start_ns: int,
        end_ns: int,
    ) -> float:
        duration_ns = max(end_ns - start_ns, 0)
        return duration_ns / 1_000_000
