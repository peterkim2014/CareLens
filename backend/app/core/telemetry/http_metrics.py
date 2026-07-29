from dataclasses import dataclass
from threading import Lock


@dataclass(
    frozen=True,
    slots=True,
)
class HTTPRequestCountSnapshot:
    method: str
    route: str
    status_code: int
    count: int


@dataclass(
    frozen=True,
    slots=True,
)
class HTTPRequestDurationSnapshot:
    method: str
    route: str
    count: int
    total_duration_seconds: float


@dataclass(
    frozen=True,
    slots=True,
)
class HTTPMetricsSnapshot:
    requests: tuple[HTTPRequestCountSnapshot, ...]
    durations: tuple[HTTPRequestDurationSnapshot, ...]
    requests_in_progress: int


class HTTPMetrics:
    def __init__(
        self,
    ) -> None:
        self._lock = Lock()

        self._request_counts: dict[
            tuple[str, str, int],
            int,
        ] = {}

        self._request_duration_counts: dict[
            tuple[str, str],
            int,
        ] = {}

        self._request_duration_totals: dict[
            tuple[str, str],
            float,
        ] = {}

        self._requests_in_progress = 0

    def record_request_started(
        self,
    ) -> None:
        with self._lock:
            self._requests_in_progress += 1

    def record_request_completed(
        self,
        *,
        method: str,
        route: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        normalized_method = method.upper()
        normalized_duration = max(
            duration_seconds,
            0.0,
        )

        request_key = (
            normalized_method,
            route,
            status_code,
        )

        duration_key = (
            normalized_method,
            route,
        )

        with self._lock:
            self._requests_in_progress = max(
                self._requests_in_progress - 1,
                0,
            )

            self._request_counts[request_key] = (
                self._request_counts.get(
                    request_key,
                    0,
                )
                + 1
            )

            self._request_duration_counts[duration_key] = (
                self._request_duration_counts.get(
                    duration_key,
                    0,
                )
                + 1
            )

            self._request_duration_totals[duration_key] = (
                self._request_duration_totals.get(
                    duration_key,
                    0.0,
                )
                + normalized_duration
            )

    def snapshot(
        self,
    ) -> HTTPMetricsSnapshot:
        with self._lock:
            requests = tuple(
                HTTPRequestCountSnapshot(
                    method=method,
                    route=route,
                    status_code=status_code,
                    count=count,
                )
                for (
                    method,
                    route,
                    status_code,
                ), count in sorted(
                    self._request_counts.items(),
                )
            )

            durations = tuple(
                HTTPRequestDurationSnapshot(
                    method=method,
                    route=route,
                    count=self._request_duration_counts[
                        (
                            method,
                            route,
                        )
                    ],
                    total_duration_seconds=total,
                )
                for (
                    method,
                    route,
                ), total in sorted(
                    self._request_duration_totals.items(),
                )
            )

            return HTTPMetricsSnapshot(
                requests=requests,
                durations=durations,
                requests_in_progress=(
                    self._requests_in_progress
                ),
            )