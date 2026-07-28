"""Tests for liveness and database-readiness endpoints."""

import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.config import Settings
from app.main import create_app

TEST_DATABASE_URL = "postgresql+psycopg://unused:unused@localhost:5432/" "verdeza_readiness_test"


class FakeResult:
    """Minimal SQLAlchemy result supporting scalar_one()."""

    def __init__(self) -> None:
        self.scalar_one_calls = 0

    def scalar_one(self) -> int:
        self.scalar_one_calls += 1
        return 1


class FakeSession:
    """Context-managed SQLAlchemy session test double."""

    def __init__(
        self,
        *,
        result: FakeResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result or FakeResult()
        self.error = error
        self.execute_calls = 0
        self.closed = False

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ) -> bool:
        self.closed = True
        return False

    def execute(self, statement):
        self.execute_calls += 1

        if self.error is not None:
            raise self.error

        return self.result


def make_application(session_factory):
    """Build a test application with an explicit readiness factory."""

    settings = Settings(
        APP_ENV="test",
        SECRET_KEY="",
        DATABASE_URL=TEST_DATABASE_URL,
    )

    application = create_app(settings)

    # This verifies that /ready reads the factory from request.app.state.
    application.state.session_factory = session_factory

    return application


@pytest.mark.api
def test_health_is_database_independent(app_client):
    """The liveness endpoint must not require database connectivity."""

    response = app_client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "X-Request-ID" in response.headers


@pytest.mark.api
def test_ready_uses_request_application_session_factory():
    """A successful SELECT 1 returns ready and closes the session."""

    result = FakeResult()
    session = FakeSession(result=result)

    application = make_application(lambda: session)

    with TestClient(application) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    assert "X-Request-ID" in response.headers

    assert session.execute_calls == 1
    assert result.scalar_one_calls == 1
    assert session.closed is True


@pytest.mark.api
def test_ready_sqlalchemy_failure_returns_safe_503(caplog):
    """SQLAlchemy failures are logged but not exposed to the client."""

    request_id = "44444444-4444-4444-4444-444444444444"

    database_error = OperationalError(
        "SELECT 1",
        {},
        RuntimeError("private database connection failure"),
    )

    session = FakeSession(error=database_error)
    application = make_application(lambda: session)

    with (
        caplog.at_level(
            logging.WARNING,
            logger="verdeza",
        ),
        TestClient(
            application,
            raise_server_exceptions=False,
        ) as client,
    ):
        response = client.get(
            "/ready",
            headers={"X-Request-ID": request_id},
        )

    assert response.status_code == 503

    error = response.json()["error"]

    assert error["code"] == "DATABASE_UNAVAILABLE"
    assert error["message"] == "The service is temporarily unavailable."
    assert error["request_id"] == request_id
    assert response.headers["X-Request-ID"] == request_id

    # Database details must never reach the API client.
    assert "private database connection failure" not in response.text
    assert "OperationalError" not in response.text
    assert "SELECT 1" not in response.text
    assert TEST_DATABASE_URL not in response.text

    readiness_records = [
        record
        for record in caplog.records
        if record.name == "verdeza" and "readiness_failed" in record.getMessage()
    ]

    assert len(readiness_records) == 1

    record = readiness_records[0]

    assert request_id in record.getMessage()
    assert "OperationalError" in record.getMessage()
    assert record.exc_info is not None
    assert isinstance(
        record.exc_info[1],
        OperationalError,
    )
    assert session.closed is True


@pytest.mark.api
def test_ready_programming_error_uses_global_500():
    """Non-SQLAlchemy defects must not be labelled as database outages."""

    session = FakeSession(error=RuntimeError("private programming defect"))

    application = make_application(lambda: session)

    with TestClient(
        application,
        raise_server_exceptions=False,
    ) as client:
        response = client.get("/ready")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "private programming defect" not in response.text
    assert "DATABASE_UNAVAILABLE" not in response.text
    assert "X-Request-ID" in response.headers
    assert session.closed is True
