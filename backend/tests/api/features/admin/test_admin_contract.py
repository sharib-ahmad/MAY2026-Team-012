"""Contract and access-control tests for the administrator API."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status

from app.models.enums import Role


@pytest.mark.api
def test_runtime_exposes_the_approved_admin_contract(app_test):
    routes = {
        (method, route.path)
        for route in app_test.routes
        for method in getattr(route, "methods", set())
    }

    required = {
        ("POST", "/api/v1/admin/users"),
        ("GET", "/api/v1/admin/users"),
        ("PATCH", "/api/v1/admin/users/{user_id}"),
        ("GET", "/api/v1/wards"),
        ("GET", "/api/v1/admin/wards"),
        ("POST", "/api/v1/admin/wards"),
        ("PATCH", "/api/v1/admin/wards/{ward_id}"),
        ("DELETE", "/api/v1/admin/wards/{ward_id}"),
        ("GET", "/api/v1/admin/dashboard"),
        ("GET", "/api/v1/admin/logs"),
    }
    forbidden = {
        ("GET", "/api/v1/zones"),
        ("GET", "/api/v1/admin/ward"),
        ("POST", "/api/v1/admin/ward"),
        ("PATCH", "/api/v1/admin/ward/{ward_id}"),
        ("DELETE", "/api/v1/admin/ward/{ward_id}"),
        ("POST", "/api/v1/admin/account"),
        ("POST", "/api/v1/admin/user"),
        ("PATCH", "/api/v1/admin/user/{user_id}"),
        ("PATCH", "/api/v1/admin/user/{user_id}/status"),
        ("DELETE", "/api/v1/admin/user/{user_id}"),
    }

    assert required <= routes
    assert forbidden.isdisjoint(routes)


def _endpoint_request(client, paths, key, headers=None):
    user_id = uuid.uuid4()
    ward_id = uuid.uuid4()
    headers = headers or {}

    if key == "dashboard":
        return client.get(paths.dashboard, headers=headers)
    if key == "logs":
        return client.get(paths.logs, headers=headers)
    if key == "list-users":
        return client.get(paths.list_users, headers=headers)
    if key == "create-user":
        return client.post(
            paths.create_user,
            headers=headers,
            json={
                "name": "Access Test",
                "email": f"access-{uuid.uuid4().hex}@example.com",
                "phone": f"+91{uuid.uuid4().int % 10**10:010d}",
                "password": "StrongPass123!",
                "role": "CITIZEN" if paths.canonical_users else "RESIDENT",
            },
        )
    if key == "update-user":
        return client.patch(
            paths.update_user.format(user_id=user_id),
            headers=headers,
            json={"name": "Denied Update"},
        )
    if key == "update-status":
        return client.patch(
            paths.update_status.format(user_id=user_id),
            headers=headers,
            json={"status": "DISABLED"},
        )
    if key == "list-wards":
        return client.get(paths.ward_collection, headers=headers)
    if key == "create-ward":
        return client.post(
            paths.ward_collection,
            headers=headers,
            json={"code": f"W-{uuid.uuid4().hex[:4]}", "name": "Denied Ward"},
        )
    if key == "update-ward":
        return client.patch(
            paths.ward_item.format(ward_id=ward_id),
            headers=headers,
            json={"name": "Denied Ward", "sectors": None},
        )
    if key == "delete-ward":
        return client.delete(paths.ward_item.format(ward_id=ward_id), headers=headers)
    raise AssertionError(f"Unknown endpoint key: {key}")


@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize(
    "endpoint_key",
    [
        "dashboard",
        "logs",
        "list-users",
        "create-user",
        "update-user",
        "update-status",
        "list-wards",
        "create-ward",
        "update-ward",
        "delete-ward",
    ],
)
def test_every_admin_endpoint_rejects_missing_credentials_with_401(
    db_client,
    admin_paths,
    endpoint_key,
    assert_safe_error,
):
    response = _endpoint_request(db_client, admin_paths, endpoint_key)

    error = assert_safe_error(
        response,
        status.HTTP_401_UNAUTHORIZED,
        "AUTHENTICATION_REQUIRED",
    )
    assert response.headers.get("WWW-Authenticate") == "Bearer"
    assert "admin" not in error["message"].lower()


@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize(
    "endpoint_key",
    [
        "dashboard",
        "logs",
        "list-users",
        "create-user",
        "update-user",
        "update-status",
        "list-wards",
        "create-ward",
        "update-ward",
        "delete-ward",
    ],
)
def test_every_admin_endpoint_rejects_non_admin_roles(
    db_client,
    admin_paths,
    make_user,
    bearer_for,
    endpoint_key,
    assert_safe_error,
):
    citizen = make_user(role=Role.CITIZEN)

    response = _endpoint_request(
        db_client,
        admin_paths,
        endpoint_key,
        headers=bearer_for(citizen),
    )

    assert_safe_error(response, status.HTTP_403_FORBIDDEN, "FORBIDDEN")
