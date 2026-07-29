from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(
    app,
    raise_server_exceptions=False,
)


def test_response_receives_generated_trace_id() -> None:
    response = client.get(
        "/api/v1/health",
    )

    assert response.status_code == 200

    trace_header = response.headers["X-Trace-ID"]

    assert UUID(trace_header)


def test_valid_client_trace_id_is_preserved() -> None:
    trace_id = uuid4()

    response = client.get(
        "/api/v1/health",
        headers={
            "X-Trace-ID": str(trace_id),
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Trace-ID"] == str(trace_id)


def test_invalid_client_trace_id_is_replaced() -> None:
    response = client.get(
        "/api/v1/health",
        headers={
            "X-Trace-ID": "not-a-valid-uuid",
        },
    )

    assert response.status_code == 200

    returned_trace_id = response.headers["X-Trace-ID"]

    assert returned_trace_id != "not-a-valid-uuid"
    assert UUID(returned_trace_id)


def test_analysis_uses_request_trace_id() -> None:
    trace_id = uuid4()

    response = client.post(
        "/api/v1/analysis",
        headers={
            "X-Trace-ID": str(trace_id),
        },
        json={
            "text": ("What symptoms do seasonal allergies cause?"),
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["trace_id"] == str(trace_id)
    assert response.headers["X-Trace-ID"] == str(trace_id)


def test_validation_error_includes_trace_id() -> None:
    trace_id = uuid4()

    response = client.post(
        "/api/v1/analysis",
        headers={
            "X-Trace-ID": str(trace_id),
        },
        json={
            "text": "",
        },
    )

    assert response.status_code == 422

    body = response.json()

    assert body["error"]["trace_id"] == str(trace_id)
    assert response.headers["X-Trace-ID"] == str(trace_id)
