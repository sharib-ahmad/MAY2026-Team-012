"""Focused fixtures for SCRUM-173 administrator API QA."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.features.users.models import User
from app.models.enums import Role, UserStatus
from app.models.zone import Zone


@dataclass(frozen=True, slots=True)
class AdminPaths:
    """Current preferred routes, with isolated fallbacks for legacy aliases."""

    create_user: str
    list_users: str
    update_user: str
    update_status: str
    delete_user: str
    ward_collection: str
    ward_item: str
    ward_reference: str
    dashboard: str
    logs: str
    login: str
    me: str
    has_list_users: bool


def _runtime_routes(app_test) -> set[tuple[str, str]]:
    return {
        (method, route.path)
        for route in app_test.routes
        for method in getattr(route, "methods", set())
    }


@pytest.fixture
def admin_paths(app_test) -> AdminPaths:
    routes = _runtime_routes(app_test)

    return AdminPaths(
        create_user=(
            "/api/v1/admin/users"
            if ("POST", "/api/v1/admin/users") in routes
            else "/api/v1/admin/user"
        ),
        list_users="/api/v1/admin/users",
        update_user=(
            "/api/v1/admin/users/{user_id}"
            if ("PATCH", "/api/v1/admin/users/{user_id}") in routes
            else "/api/v1/admin/user/{user_id}"
        ),
        update_status=(
            "/api/v1/admin/users/{user_id}/status"
            if ("PATCH", "/api/v1/admin/users/{user_id}/status") in routes
            else "/api/v1/admin/user/{user_id}/status"
        ),
        delete_user=(
            "/api/v1/admin/users/{user_id}"
            if ("DELETE", "/api/v1/admin/users/{user_id}") in routes
            else "/api/v1/admin/user/{user_id}"
        ),
        ward_collection=(
            "/api/v1/admin/wards"
            if ("GET", "/api/v1/admin/wards") in routes
            else "/api/v1/admin/ward"
        ),
        ward_item=(
            "/api/v1/admin/wards/{ward_id}"
            if ("PATCH", "/api/v1/admin/wards/{ward_id}") in routes
            else "/api/v1/admin/ward/{ward_id}"
        ),
        ward_reference="/api/v1/wards",
        dashboard="/api/v1/admin/dashboard",
        logs="/api/v1/admin/logs",
        login=(
            "/api/v1/auth/login" if ("POST", "/api/v1/auth/login") in routes else "/api/v1/login"
        ),
        me=("/api/v1/auth/me" if ("GET", "/api/v1/auth/me") in routes else "/api/v1/me"),
        has_list_users=("GET", "/api/v1/admin/users") in routes,
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
    _paths: AdminPaths,
    *,
    name: str,
    email: str,
    phone: str,
    password: str,
    role: Role,
    ward: Zone | None = None,
) -> dict[str, object]:
    """Build a valid request that reaches the current administrator service."""

    payload: dict[str, object] = {
        "name": name,
        "email": email,
        "phone": phone,
        "password": password,
        "role": role.value,
    }
    if ward is not None:
        payload["zone_id"] = str(ward.id)
    return payload


def _role_update_payload(_paths: AdminPaths, role: Role) -> dict[str, str]:
    return {"role": role.value}


def _status_update_payload(_paths: AdminPaths, user_status: UserStatus) -> dict[str, str]:
    return {"status": user_status.value}


def _extract_user_body(response) -> dict[str, Any]:
    body = response.json()
    if isinstance(body, dict) and isinstance(body.get("user"), dict):
        return body["user"]
    assert isinstance(body, dict)
    return body


def _iter_json_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _iter_json_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_json_keys(child)


def _assert_no_internal_error_details(response, *, secret_values: Iterable[str] = ()) -> None:
    text = response.text.lower()
    forbidden_markers = (
        "traceback",
        "sqlalchemy",
        "psycopg",
        "secret_key",
        "private_table",
    )
    for marker in forbidden_markers:
        assert marker not in text
    for value in secret_values:
        if value:
            assert value.lower() not in text


def _assert_safe_public_body(
    response,
    *,
    additional_forbidden_keys: Iterable[str] = (),
) -> None:
    """Reject sensitive response fields without rejecting safe validation locations."""

    body = response.json()
    keys = {key.lower() for key in _iter_json_keys(body)}
    forbidden_keys = {
        "password_hash",
        "token_version",
        "deleted_at",
        "secret_key",
    }
    forbidden_keys.update(key.lower() for key in additional_forbidden_keys)
    assert keys.isdisjoint(forbidden_keys), f"Sensitive response keys: {keys & forbidden_keys}"
    _assert_no_internal_error_details(response)


def _assert_safe_error(
    response,
    expected_status: int | set[int],
    expected_code: str | set[str] | None = None,
    *,
    secret_values: Iterable[str] = (),
) -> dict[str, Any]:
    allowed_statuses = {expected_status} if isinstance(expected_status, int) else expected_status
    assert response.status_code in allowed_statuses, response.text

    body = response.json()
    assert set(body) == {"error"}
    error = body["error"]
    assert {"code", "message", "request_id"} <= set(error)
    assert isinstance(error["message"], str) and error["message"].strip()

    if expected_code is not None:
        allowed_codes = {expected_code} if isinstance(expected_code, str) else expected_code
        assert error["code"] in allowed_codes

    assert response.headers.get("X-Request-ID") == error["request_id"]
    _assert_no_internal_error_details(response, secret_values=secret_values)
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
