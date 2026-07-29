from contextvars import ContextVar, Token
from uuid import UUID, uuid4

_trace_id_context: ContextVar[UUID | None] = ContextVar(
    "trace_id",
    default=None,
)


def get_trace_id() -> UUID | None:
    return _trace_id_context.get()


def get_or_create_trace_id() -> UUID:
    trace_id = get_trace_id()

    if trace_id is not None:
        return trace_id

    return uuid4()


def set_trace_id(
    trace_id: UUID,
) -> Token[UUID | None]:
    return _trace_id_context.set(trace_id)


def reset_trace_id(
    token: Token[UUID | None],
) -> None:
    _trace_id_context.reset(token)
