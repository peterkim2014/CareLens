from app.ai.observability import (
    PipelineAuditRecorder,
    PipelineEventStatus,
)


def test_recorder_creates_completed_stage_event() -> None:
    recorder = PipelineAuditRecorder()
    timer = recorder.start_stage()

    recorder.complete_stage(
        stage="risk_assessed",
        timer=timer,
        metadata={
            "risk_level": "routine",
        },
    )

    audit = recorder.build()

    assert len(audit.events) == 1

    event = audit.events[0]

    assert event.stage == "risk_assessed"
    assert event.status is PipelineEventStatus.COMPLETED
    assert event.duration_ms >= 0
    assert event.metadata == {
        "risk_level": "routine",
    }


def test_recorder_creates_failed_stage_event() -> None:
    recorder = PipelineAuditRecorder()
    timer = recorder.start_stage()

    recorder.fail_stage(
        stage="response_generated",
        timer=timer,
        error_type="RuntimeError",
    )

    audit = recorder.build()

    assert len(audit.events) == 1

    event = audit.events[0]

    assert event.stage == "response_generated"
    assert event.status is PipelineEventStatus.FAILED
    assert event.duration_ms >= 0
    assert event.metadata == {
        "error_type": "RuntimeError",
    }


def test_audit_contains_total_duration() -> None:
    recorder = PipelineAuditRecorder()

    timer = recorder.start_stage()
    recorder.complete_stage(
        stage="intake_validated",
        timer=timer,
    )

    audit = recorder.build()

    assert audit.total_duration_ms >= 0
    assert audit.completed_at >= audit.started_at


def test_build_returns_copy_of_events() -> None:
    recorder = PipelineAuditRecorder()

    timer = recorder.start_stage()
    recorder.complete_stage(
        stage="intake_validated",
        timer=timer,
    )

    first_audit = recorder.build()
    first_audit.events.clear()

    second_audit = recorder.build()

    assert len(second_audit.events) == 1
