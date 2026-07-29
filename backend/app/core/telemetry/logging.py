import json
import logging
from datetime import UTC, datetime
from typing import Any, ClassVar

from app.core.telemetry.context import get_trace_id


class StructuredJSONFormatter(logging.Formatter):
    _reserved_attributes: ClassVar[frozenset[str]] = frozenset(
        {
            "args",
            "asctime",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "taskName",
            "thread",
            "threadName",
        }
    )

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        trace_id = get_trace_id()

        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if trace_id is not None:
            payload["trace_id"] = str(trace_id)

        for key, value in record.__dict__.items():
            if key in self._reserved_attributes:
                continue

            if key.startswith("_"):
                continue

            payload[key] = value

        return json.dumps(
            payload,
            default=str,
            separators=(",", ":"),
        )


def configure_logging(
    *,
    debug: bool,
) -> None:
    root_logger = logging.getLogger()

    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJSONFormatter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    logging.getLogger("uvicorn.access").disabled = True
