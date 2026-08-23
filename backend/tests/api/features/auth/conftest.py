"""Focused fixtures for SCRUM-88 authentication QA."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from jose import jwt

from app.core.config import get_settings
from app.core.security import get_password_hash
from app.features.users.models import User
from app.models.enums import Role, UserStatus


@pytest.fixture
def auth_paths(app_test) -> dict[str, str]:
    """Use current paths for behaviour tests while contract tests enforce approved paths."""

    routes = {
        (method, route.path)
        for route in app_test.routes
        for method in getattr(route, "methods", set())
    }

    login = "/api/v1/auth/login" if ("POST", "/api/v1/auth/login") in routes else "/api/v1/login"
    me = "/api/v1/auth/me" if ("GET", "/api/v1/auth/me") in routes else "/api/v1/me"

    return {"login": login, "me": me}


@pytest.fixture
def make_user(db) -> Callable[..., User]:
    """Persist a user with safe deterministic defaults and optional overrides."""

    def _make(**overrides: Any) -> User:
        suffix = uuid.uuid4().hex[:12]
        password = overrides.pop("password", "StrongPassword123!")

        values: dict[str, Any] = {
            "name": "Authentication Test User",
            "email": f"auth-{suffix}@example.com",
            "password_hash": get_password_hash(password),
            "phone": f"+91{uuid.uuid4().int % 10**10:010d}",
            "role": Role.CITIZEN,
            "status": UserStatus.ACTIVE,
            "token_version": 1,
        }
        values.update(overrides)

        user = User(**values)
        db.add(user)
        db.flush()

        return user

    return _make


@pytest.fixture
def signed_token() -> Callable[..., str]:
    """Create signed JWTs with explicit claims for positive and negative cases."""

    settings = get_settings()

    def _sign(
        *,
        subject: str | None = None,
        token_version: int | None = None,
        include_subject: bool = True,
        include_token_version: bool = True,
        expires_at: datetime | None = None,
        secret: str | None = None,
    ) -> str:
        claims: dict[str, Any] = {
            "exp": expires_at or datetime.now(UTC) + timedelta(minutes=10),
        }

        if include_subject:
            claims["sub"] = subject or ""

        if include_token_version:
            claims["token_version"] = token_version

        return jwt.encode(
            claims,
            secret or settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

    return _sign


@pytest.fixture
def bearer_for(signed_token) -> Callable[..., dict[str, str]]:
    """Return an Authorization header for a user with controllable claims."""

    def _bearer(
        user: User,
        *,
        token_version: int | None = None,
        include_token_version: bool = True,
        expires_at: datetime | None = None,
    ) -> dict[str, str]:
        version = user.token_version if token_version is None else token_version

        token = signed_token(
            subject=str(user.id),
            token_version=version,
            include_token_version=include_token_version,
            expires_at=expires_at,
        )

        return {"Authorization": f"Bearer {token}"}

    return _bearer


@pytest.fixture
def assert_safe_error() -> Callable[..., dict[str, Any]]:
    """Assert the shared error envelope, request-ID correlation and leak protection."""

    def _assert(
        response,
        *,
        status_code: int,
        code: str,
        require_bearer_challenge: bool = False,
        forbidden_values: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        assert response.status_code == status_code, (
            f"Expected HTTP {status_code}, got {response.status_code}: {response.text}"
        )

        request_id = response.headers.get("X-Request-ID")
        assert request_id
        uuid.UUID(request_id)

        body = response.json()

        assert set(body) == {"error"}
        assert body["error"]["code"] == code
        assert body["error"]["request_id"] == request_id
        assert isinstance(body["error"]["message"], str)
        assert body["error"]["message"]

        if require_bearer_challenge:
            assert response.headers.get("WWW-Authenticate") == "Bearer"

        response_text = response.text.lower()

        forbidden_fragments = (
            "password_hash",
            "secret_key",
            "sqlstate",
            "constraint_name",
            "traceback",
            "select ",
            "insert ",
            "update users",
        )

        for fragment in forbidden_fragments:
            assert fragment not in response_text

        for value in forbidden_values:
            if value:
                assert value.lower() not in response_text

        return body

    return _assert
