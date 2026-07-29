from uuid import UUID, uuid4

from app.core.telemetry import (
    get_or_create_trace_id,
    get_trace_id,
    reset_trace_id,
    set_trace_id,
)


def test_trace_context_is_empty_by_default() -> None:
    assert get_trace_id() is None


def test_trace_context_stores_trace_id() -> None:
    trace_id = uuid4()
    token = set_trace_id(trace_id)

    try:
        assert get_trace_id() == trace_id
        assert get_or_create_trace_id() == trace_id
    finally:
        reset_trace_id(token)

    assert get_trace_id() is None


def test_get_or_create_trace_id_creates_unstored_uuid() -> None:
    first_trace_id = get_or_create_trace_id()
    second_trace_id = get_or_create_trace_id()

    assert isinstance(first_trace_id, UUID)
    assert isinstance(second_trace_id, UUID)

    assert first_trace_id != second_trace_id
    assert get_trace_id() is None


def test_get_or_create_trace_id_reuses_context_value() -> None:
    context_trace_id = uuid4()
    token = set_trace_id(context_trace_id)

    try:
        first_trace_id = get_or_create_trace_id()
        second_trace_id = get_or_create_trace_id()

        assert first_trace_id == context_trace_id
        assert second_trace_id == context_trace_id
        assert get_trace_id() == context_trace_id
    finally:
        reset_trace_id(token)

    assert get_trace_id() is None
