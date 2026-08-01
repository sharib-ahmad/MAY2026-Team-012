"""Contract and access-control tests for the administrator API."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

import pytest
from fastapi import status

from app.models.enums import Role

APPROVED_RUNTIME_ROUTES = {
    ("POST", "/api/v1/admin/users"),
    ("GET", "/api/v1/admin/users"),
    ("PATCH", "/api/v1/admin/users/{user_id}"),
    ("PATCH", "/api/v1/admin/users/{user_id}/status"),
    ("GET", "/api/v1/wards"),
    ("GET", "/api/v1/admin/wards"),
    ("POST", "/api/v1/admin/wards"),
    ("PATCH", "/api/v1/admin/wards/{ward_id}"),
    ("DELETE", "/api/v1/admin/wards/{ward_id}"),
    ("GET", "/api/v1/admin/dashboard"),
    ("GET", "/api/v1/admin/logs"),
}

LEGACY_DOCUMENTED_PATHS = {
    "/api/v1/admin/account",
    "/api/v1/admin/user",
    "/api/v1/admin/user/{user_id}",
    "/api/v1/admin/user/{user_id}/status",
    "/api/v1/admin/ward",
    "/api/v1/admin/ward/{ward_id}",
    "/api/v1/zones",
}


def _runtime_routes(app_test) -> set[tuple[str, str]]:
    return {
        (method, route.path)
        for route in app_test.routes
        for method in getattr(route, "methods", set())
    }


def _documented_paths_from_static_yaml() -> set[str]:
    repository_root = Path(__file__).resolve().parents[5]
    yaml_text = (repository_root / "api-doc.yaml").read_text(encoding="utf-8")
    return set(re.findall(r"^  (/[^:]+):\s*$", yaml_text, flags=re.MULTILINE))


@pytest.mark.api
def test_runtime_exposes_the_approved_admin_contract(app_test):
    routes = _runtime_routes(app_test)
    missing = APPROVED_RUNTIME_ROUTES - routes

    assert not missing, f"Missing approved administrator routes: {sorted(missing)}"


@pytest.mark.api
def test_openapi_publishes_canonical_paths_without_legacy_aliases(app_test):
    openapi_paths = set(app_test.openapi()["paths"])
    required_paths = {path for _, path in APPROVED_RUNTIME_ROUTES}

    assert required_paths <= openapi_paths

    published_legacy_paths = LEGACY_DOCUMENTED_PATHS & openapi_paths
    assert not published_legacy_paths, (
        f"OpenAPI still publishes legacy administrator paths: {sorted(published_legacy_paths)}"
    )


@pytest.mark.api
def test_static_swagger_documents_the_approved_admin_paths():
    documented_paths = _documented_paths_from_static_yaml()
    required_paths = {path for _, path in APPROVED_RUNTIME_ROUTES}
    missing = required_paths - documented_paths

    assert not missing, f"api-doc.yaml is missing administrator paths: {sorted(missing)}"


def _endpoint_request(client, paths, key, headers=None):
    user_id = uuid.uuid4()
    ward_id = uuid.uuid4()
    headers = headers or {}

    if key == "dashboard":
        return client.get(paths.dashboard, headers=headers)
    if key == "logs":
        return client.get(paths.logs, headers=headers)
    if key == "ward-reference":
        return client.get(paths.ward_reference, headers=headers)
    if key == "create-user":
        return client.post(
            paths.create_user,
            headers=headers,
            json={
                "name": "Access Test",
                "email": f"access-{uuid.uuid4().hex}@example.com",
                "phone": f"+91{uuid.uuid4().int % 10**10:010d}",
                "password": "StrongPass123!",
                "role": "CITIZEN",
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


PROTECTED_ENDPOINT_KEYS = [
    "dashboard",
    "logs",
    "ward-reference",
    "create-user",
    "update-user",
    "update-status",
    "list-wards",
    "create-ward",
    "update-ward",
    "delete-ward",
]


@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize("endpoint_key", PROTECTED_ENDPOINT_KEYS)
def test_every_exposed_admin_endpoint_rejects_missing_credentials_with_401(
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
    assert "admin" not in error["message"].lower()


@pytest.mark.api
@pytest.mark.security
def test_missing_credentials_include_the_bearer_challenge(
    db_client,
    admin_paths,
    assert_safe_error,
):
    response = db_client.get(admin_paths.dashboard)

    assert_safe_error(
        response,
        status.HTTP_401_UNAUTHORIZED,
        "AUTHENTICATION_REQUIRED",
    )
    assert response.headers.get("WWW-Authenticate") == "Bearer"


@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize(
    "role",
    [
        Role.CITIZEN,
        Role.COLLECTION_WORKER,
        Role.MUNICIPAL_OFFICER,
        Role.RECYCLER,
    ],
)
@pytest.mark.parametrize("endpoint_key", PROTECTED_ENDPOINT_KEYS)
def test_every_exposed_admin_endpoint_rejects_non_admin_roles(
    db_client,
    admin_paths,
    make_user,
    bearer_for,
    endpoint_key,
    role,
    assert_safe_error,
):
    non_admin = make_user(role=role)

    response = _endpoint_request(
        db_client,
        admin_paths,
        endpoint_key,
        headers=bearer_for(non_admin),
    )

    assert_safe_error(response, status.HTTP_403_FORBIDDEN, "FORBIDDEN")
