"""System endpoint tests: liveness independent of DB, readiness dependent."""

import pytest

from app.core.config import Settings
from app.main import create_app


@pytest.mark.api
def test_health_is_liveness_only(app_client):
    r = app_client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert "X-Request-ID" in r.headers


@pytest.mark.api
def test_ready_ok_when_db_available(db_client):
    r = db_client.get("/ready")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"
    assert "X-Request-ID" in r.headers


@pytest.mark.api
def test_ready_returns_503_when_db_unavailable():
    """Readiness must fail when the DB is down. Build the app directly
    from unavailable-database settings so no engine is orphaned."""
    from fastapi.testclient import TestClient

    dead_settings = Settings(
        APP_ENV="test",
        SECRET_KEY="",
        DATABASE_URL="postgresql+psycopg://x:x@127.0.0.1:1/verdeza_unavailable_test",
    )
    application = create_app(dead_settings)
    with TestClient(application, raise_server_exceptions=False) as client:
        ready_response = client.get("/ready")
        health_response = client.get("/health")
    assert ready_response.status_code == 503
    assert ready_response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert "X-Request-ID" in ready_response.headers
    assert health_response.status_code == 200
