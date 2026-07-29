from uuid import uuid4

from app.ai.observability import PipelineAuditRecorder
from app.core.errors import AnalysisPipelineError


def test_pipeline_error_preserves_failure_context() -> None:
    trace_id = uuid4()
    recorder = PipelineAuditRecorder()

    timer = recorder.start_stage()

    recorder.fail_stage(
        stage="evidence_retrieved",
        timer=timer,
        error_type="RuntimeError",
    )

    audit = recorder.build()

    error = AnalysisPipelineError(
        trace_id=trace_id,
        failed_stage="evidence_retrieved",
        audit=audit,
        retryable=True,
    )

    assert error.trace_id == trace_id
    assert error.failed_stage == "evidence_retrieved"
    assert error.audit == audit
    assert error.retryable is True


def test_pipeline_error_message_excludes_original_exception() -> None:
    trace_id = uuid4()
    recorder = PipelineAuditRecorder()

    error = AnalysisPipelineError(
        trace_id=trace_id,
        failed_stage="response_generated",
        audit=recorder.build(),
        retryable=True,
    )

    assert str(error) == ("Analysis pipeline failed at stage: response_generated")
