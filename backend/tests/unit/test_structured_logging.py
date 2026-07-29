import json
import logging
from uuid import uuid4

from app.core.telemetry import (
    StructuredJSONFormatter,
    reset_trace_id,
    set_trace_id,
)


def test_formatter_outputs_structured_json() -> None:
    formatter = StructuredJSONFormatter()

    record = logging.LogRecord(
        name="carelens.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Pipeline completed",
        args=(),
        exc_info=None,
    )

    record.event = "pipeline_completed"
    record.duration_ms = 12.5

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "carelens.test"
    assert payload["message"] == "Pipeline completed"
    assert payload["event"] == "pipeline_completed"
    assert payload["duration_ms"] == 12.5
    assert payload["timestamp"]


def test_formatter_includes_context_trace_id() -> None:
    trace_id = uuid4()
    token = set_trace_id(trace_id)

    try:
        formatter = StructuredJSONFormatter()

        record = logging.LogRecord(
            name="carelens.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Request completed",
            args=(),
            exc_info=None,
        )

        payload = json.loads(formatter.format(record))

        assert payload["trace_id"] == str(trace_id)
    finally:
        reset_trace_id(token)


def test_formatter_does_not_add_query_text() -> None:
    formatter = StructuredJSONFormatter()

    private_query = "This clinical query must never be logged."

    record = logging.LogRecord(
        name="carelens.test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="Analysis failed",
        args=(),
        exc_info=None,
    )

    serialized_log = formatter.format(record)

    assert private_query not in serialized_log
