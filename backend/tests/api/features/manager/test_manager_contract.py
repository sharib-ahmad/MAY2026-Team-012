"""Contract, authentication and role-boundary tests for SCRUM-174."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi import status

from app.models.enums import Role

REQUIRED_CANONICAL_ROUTES = {
    ("GET", "/api/v1/complaints"),
    ("PATCH", "/api/v1/complaints/{complaint_id}/resolution"),
    ("GET", "/api/v1/bulk-pickups"),
    ("PATCH", "/api/v1/bulk-pickups/{bulk_pickup_id}"),
    ("GET", "/api/v1/notifications/me"),
}

DUPLICATE_MANAGER_WRITE_ROUTES = {
    ("PATCH", "/api/v1/manager/tickets/{ticket_id}"),
    ("POST", "/api/v1/manager/bulk-pickups/{request_id}/assign"),
}


@pytest.mark.api
def test_runtime_uses_the_approved_resource_contract(app_test):
    routes = {
        (method, route.path)
        for route in app_test.routes
        for method in getattr(route, "methods", set())
    }

    assert routes >= REQUIRED_CANONICAL_ROUTES
    assert DUPLICATE_MANAGER_WRITE_ROUTES.isdisjoint(routes)


@pytest.mark.api
def test_every_exposed_manager_route_is_documented_in_swagger(app_test):
    yaml_text = Path("../api-doc.yaml").read_text(encoding="utf-8")
    manager_paths = {
        route.path for route in app_test.routes if route.path.startswith("/api/v1/manager/")
    }

    assert manager_paths
    undocumented = sorted(path for path in manager_paths if f"{path}:" not in yaml_text)
    assert undocumented == []


def _request_manager_endpoint(client, paths, endpoint: str, *, headers=None):
    headers = headers or {}
    object_id = uuid.uuid4()

    if endpoint == "dashboard":
        return client.get(paths.dashboard, headers=headers)
    if endpoint == "notifications-read":
        return client.patch(paths.notifications_read, headers=headers)
    if endpoint == "ticket-update":
        return client.patch(
            paths.ticket_update.format(ticket_id=object_id),
            headers=headers,
            json={"status": "RESOLVED", "resolution_notes": "Cleared safely."},
        )
    if endpoint == "bulk-assign":
        return client.post(
            paths.bulk_assign.format(request_id=object_id),
            headers=headers,
            json={"collector_id": str(uuid.uuid4())},
        )
    if endpoint == "worker-update":
        return client.patch(
            paths.worker_update.format(worker_id=object_id),
            headers=headers,
            json={"name": "QA Worker", "phone": "1234567890", "status": "ACTIVE"},
        )
    if endpoint == "worker-delete":
        return client.delete(
            paths.worker_delete.format(worker_id=object_id),
            headers=headers,
        )
    raise AssertionError(f"Unknown endpoint key: {endpoint}")


@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize(
    "endpoint",
    [
        "dashboard",
        "notifications-read",
        "ticket-update",
        "bulk-assign",
        "worker-update",
        "worker-delete",
    ],
)
def test_every_manager_endpoint_rejects_missing_credentials_with_bearer_challenge(
    db_client,
    manager_paths,
    assert_safe_error,
    endpoint,
):
    response = _request_manager_endpoint(db_client, manager_paths, endpoint)

    assert_safe_error(response, status.HTTP_401_UNAUTHORIZED, "AUTHENTICATION_REQUIRED")
    assert response.headers.get("WWW-Authenticate") == "Bearer"


@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize(
    "role",
    [
        Role.CITIZEN,
        Role.COLLECTION_WORKER,
        Role.RECYCLER,
        Role.SYSTEM_ADMIN,
    ],
)
def test_non_manager_roles_cannot_open_manager_dashboard(
    db_client,
    manager_paths,
    make_user,
    bearer_for,
    assert_safe_error,
    role,
):
    user = make_user(role=role)

    response = db_client.get(manager_paths.dashboard, headers=bearer_for(user))

    assert_safe_error(response, status.HTTP_403_FORBIDDEN, "FORBIDDEN")
