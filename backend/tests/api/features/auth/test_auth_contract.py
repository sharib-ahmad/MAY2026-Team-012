"""Contract and startup-security tests for SCRUM-88 authentication."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.features.auth.router import ROLE_MAP_FRONTEND_TO_DB
from app.main import create_app
from app.models.enums import Role

CANONICAL_ROUTES = {
    ("POST", "/api/v1/auth/login"),
    ("GET", "/api/v1/auth/me"),
    # DEF-004 was accepted as fixed by restricting the role field (#134 closing
    # #133), not by removing the endpoint, so registration is part of the
    # current contract: public, unauthenticated, public roles only.
    ("POST", "/api/v1/auth/register"),
}
FORBIDDEN_ROUTES = {
    ("POST", "/api/v1/register"),
    ("POST", "/api/v1/login"),
    ("GET", "/api/v1/me"),
}
# Roles a caller may self-provision without authentication. Staff roles are
# provisioned only through the System Admin flow (Story 5.1 / DEF-004).
PUBLIC_SELF_REGISTRATION_ROLES = {Role.CITIZEN, Role.COLLECTION_WORKER, Role.RECYCLER}
STAFF_ONLY_ROLES = {Role.MUNICIPAL_OFFICER, Role.SYSTEM_ADMIN}
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
    """S1-G01/S1-5101: canonical routes exist and legacy/wrong-prefix ones do not."""

    routes = _route_inventory(app_test)

    assert routes >= CANONICAL_ROUTES
    assert FORBIDDEN_ROUTES.isdisjoint(routes)


@pytest.mark.api
@pytest.mark.security
def test_public_registration_role_surface_excludes_staff_roles():
    """S1-5101/Story 5.1: the self-registration role surface is public roles only.

    Behavioural 403/200 enforcement is covered by ``test_auth_api.py``; this
    guards the mapping itself, so a newly added privileged role cannot become
    self-registerable without this contract failing first.
    """

    mapped_roles = set(ROLE_MAP_FRONTEND_TO_DB.values())

    assert STAFF_ONLY_ROLES.isdisjoint(PUBLIC_SELF_REGISTRATION_ROLES)
    assert mapped_roles - STAFF_ONLY_ROLES == PUBLIC_SELF_REGISTRATION_ROLES


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
