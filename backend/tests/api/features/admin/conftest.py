"""Focused fixtures for SCRUM-173 administrator API QA."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.features.users.models import User
from app.models.enums import Role, UserStatus
from app.models.zone import Zone


@dataclass(frozen=True, slots=True)
class AdminPaths:
    """Resolved runtime paths plus the approved canonical paths."""

    create_user: str
    list_users: str
    update_user: str
    update_status: str
    delete_user: str
    ward_collection: str
    ward_item: str
    public_wards: str
    dashboard: str
    logs: str
    login: str
    me: str
    canonical_users: bool
    canonical_wards: bool


LEGACY_ROLE_BY_CANONICAL = {
    Role.CITIZEN: "RESIDENT",
    Role.COLLECTION_WORKER: "COLLECTOR",
    Role.MUNICIPAL_OFFICER: "MANAGER",
    Role.RECYCLER: "RECYCLER",
    Role.SYSTEM_ADMIN: "ADMIN",
}


@pytest.fixture
def admin_paths(app_test) -> AdminPaths:
    routes = {
        (method, route.path)
        for route in app_test.routes
        for method in getattr(route, "methods", set())
    }

    canonical_users = {
        ("POST", "/api/v1/admin/users"),
        ("GET", "/api/v1/admin/users"),
        ("PATCH", "/api/v1/admin/users/{user_id}"),
    } <= routes

    canonical_wards = {
        ("GET", "/api/v1/admin/wards"),
        ("POST", "/api/v1/admin/wards"),
        ("PATCH", "/api/v1/admin/wards/{ward_id}"),
        ("DELETE", "/api/v1/admin/wards/{ward_id}"),
    } <= routes

    return AdminPaths(
        create_user=(
            "/api/v1/admin/users"
            if ("POST", "/api/v1/admin/users") in routes
            else "/api/v1/admin/user"
        ),
        list_users=(
            "/api/v1/admin/users"
            if ("GET", "/api/v1/admin/users") in routes
            else "/api/v1/admin/dashboard"
        ),
        update_user=(
            "/api/v1/admin/users/{user_id}" if canonical_users else "/api/v1/admin/user/{user_id}"
        ),
        update_status=(
            "/api/v1/admin/users/{user_id}"
            if canonical_users
            else "/api/v1/admin/user/{user_id}/status"
        ),
        delete_user=(
            "/api/v1/admin/users/{user_id}"
            if ("DELETE", "/api/v1/admin/users/{user_id}") in routes
            else "/api/v1/admin/user/{user_id}"
        ),
        ward_collection=("/api/v1/admin/wards" if canonical_wards else "/api/v1/admin/ward"),
        ward_item=(
            "/api/v1/admin/wards/{ward_id}" if canonical_wards else "/api/v1/admin/ward/{ward_id}"
        ),
        public_wards=("/api/v1/wards" if ("GET", "/api/v1/wards") in routes else "/api/v1/zones"),
        dashboard="/api/v1/admin/dashboard",
        logs="/api/v1/admin/logs",
        login=(
            "/api/v1/auth/login" if ("POST", "/api/v1/auth/login") in routes else "/api/v1/login"
        ),
        me=("/api/v1/auth/me" if ("GET", "/api/v1/auth/me") in routes else "/api/v1/me"),
        canonical_users=canonical_users,
        canonical_wards=canonical_wards,
    )


@pytest.fixture
def make_user(db: Session) -> Callable[..., User]:
    """Create a persisted user with unique safe defaults."""

    def _make_user(
        *,
        name: str = "QA User",
        email: str | None = None,
        phone: str | None = None,
        password: str = "StrongPass123!",
        role: Role = Role.CITIZEN,
        status: UserStatus = UserStatus.ACTIVE,
        zone: Zone | None = None,
        deleted: bool = False,
    ) -> User:
        suffix = uuid.uuid4().hex
        user = User(
            name=name,
            email=email or f"qa-{suffix}@example.com",
            phone=phone or f"+91{uuid.uuid4().int % 10**10:010d}",
            password_hash=get_password_hash(password),
            role=role,
            status=status,
            zone_id=zone.id if zone else None,
            deleted_at=datetime.now(UTC) if deleted else None,
        )
        db.add(user)
        db.flush()
        return user

    return _make_user


@pytest.fixture
def bearer_for() -> Callable[[User], dict[str, str]]:
    """Create a Bearer header for a persisted user."""

    def _bearer_for(user: User) -> dict[str, str]:
        token = create_access_token(user.id, token_version=user.token_version)
        return {"Authorization": f"Bearer {token}"}

    return _bearer_for


@pytest.fixture
def admin_user(make_user: Callable[..., User]) -> User:
    return make_user(
        name="QA Administrator",
        email="qa.admin@example.com",
        phone="+919876543230",
        role=Role.SYSTEM_ADMIN,
    )


def _user_create_payload(
    paths: AdminPaths,
    *,
    name: str,
    email: str,
    phone: str,
    password: str,
    role: Role,
    ward: Zone | None = None,
) -> dict[str, object]:
    """Build input for the current route while preserving canonical assertions."""

    if paths.canonical_users:
        payload: dict[str, object] = {
            "name": name,
            "email": email,
            "phone": phone,
            "password": password,
            "role": role.value,
        }
        if ward is not None:
            payload["ward_code"] = ward.code
        return payload

    payload = {
        "name": name,
        "email": email,
        "phone": phone,
        "password": password,
        "role": LEGACY_ROLE_BY_CANONICAL[role],
    }
    if ward is not None:
        payload["zone_id"] = str(ward.id)
    return payload


def _role_update_payload(paths: AdminPaths, role: Role) -> dict[str, str]:
    if paths.canonical_users:
        return {"role": role.value}
    return {"role": LEGACY_ROLE_BY_CANONICAL[role]}


def _status_update_payload(_paths: AdminPaths, status: UserStatus) -> dict[str, str]:
    return {"status": status.value}


def _extract_user_body(response) -> dict:
    body = response.json()
    if isinstance(body, dict) and isinstance(body.get("user"), dict):
        return body["user"]
    assert isinstance(body, dict)
    return body


def _assert_safe_public_body(response) -> None:
    text = response.text.lower()
    forbidden = (
        "password_hash",
        "token_version",
        "deleted_at",
        "traceback",
        "sqlalchemy",
        "psycopg",
        "constraint",
        "secret_key",
    )
    for term in forbidden:
        assert term not in text


def _assert_safe_error(response, expected_status: int, expected_code: str | None = None) -> dict:
    assert response.status_code == expected_status, response.text
    body = response.json()
    assert set(body) == {"error"}
    error = body["error"]
    assert {"code", "message", "request_id"} <= set(error)
    if expected_code is not None:
        assert error["code"] == expected_code
    assert response.headers.get("X-Request-ID") == error["request_id"]
    _assert_safe_public_body(response)
    return error


@pytest.fixture
def user_create_payload():
    return _user_create_payload


@pytest.fixture
def role_update_payload():
    return _role_update_payload


@pytest.fixture
def status_update_payload():
    return _status_update_payload


@pytest.fixture
def extract_user_body():
    return _extract_user_body


@pytest.fixture
def assert_safe_public_body():
    return _assert_safe_public_body


@pytest.fixture
def assert_safe_error():
    return _assert_safe_error
