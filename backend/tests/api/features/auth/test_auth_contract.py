"""Contract and startup-security tests for SCRUM-88 authentication."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

CANONICAL_ROUTES = {
    ("POST", "/api/v1/auth/login"),
    ("GET", "/api/v1/auth/me"),
}
FORBIDDEN_ROUTES = {
    ("POST", "/api/v1/register"),
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/login"),
    ("GET", "/api/v1/me"),
}
TEST_DATABASE_URL = "postgresql+psycopg://unused:unused@localhost:5432/verdeza_test"


def _route_inventory(application) -> set[tuple[str, str]]:
    return {
        (method, route.path)
        for route in application.routes
        for method in getattr(route, "methods", set())
    }


@pytest.mark.api
@pytest.mark.security
def test_runtime_exposes_only_the_approved_authentication_routes(app_test):
    """S1-G01/S1-5101: canonical routes exist and public/legacy routes do not."""

    routes = _route_inventory(app_test)

    assert routes >= CANONICAL_ROUTES
    assert FORBIDDEN_ROUTES.isdisjoint(routes)


@pytest.mark.unit
@pytest.mark.security
def test_application_startup_does_not_seed_accounts_implicitly():
    """S1-5101: normal application startup must not create known demo accounts."""

    settings = Settings(
        APP_ENV="local",
        SECRET_KEY="local-test-secret-with-at-least-thirty-two-characters",
        DATABASE_URL=TEST_DATABASE_URL,
    )
    application = create_app(settings)

    with patch("app.main.seed_database") as seed_database, TestClient(application):
        pass

    seed_database.assert_not_called()
