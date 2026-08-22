"""Contract, authentication, and role-boundary tests for SCRUM-194 Recycler QA."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status

from app.models.enums import Role

# ---------------------------------------------------------------------------
# Endpoint categorization
# ---------------------------------------------------------------------------

MANAGER_ENDPOINTS = ["manager-batches", "manager-recyclers", "manager-assign"]

RECYCLER_ENDPOINTS = [
    "recycler-batches",
    "recycler-accept",
    "recycler-reject",
    "recycler-process",
    "recycler-notifications",
    "recycler-mark-read",
    "recycler-mark-all-read",
]

ALL_ENDPOINTS = MANAGER_ENDPOINTS + RECYCLER_ENDPOINTS


def _endpoint_request(client, paths, endpoint, headers=None, json_body=None):
    """Fire a request against the named endpoint."""
    fake_id = str(uuid.uuid4())
    dispatch = {
        "manager-batches": lambda: client.get(paths.manager_batches, headers=headers),
        "manager-recyclers": lambda: client.get(paths.manager_recyclers, headers=headers),
        "manager-assign": lambda: client.post(
            paths.manager_assign.format(batch_id=fake_id),
            headers=headers,
            json=json_body or {"recycler_id": fake_id},
        ),
        "recycler-batches": lambda: client.get(paths.recycler_batches, headers=headers),
        "recycler-accept": lambda: client.post(
            paths.recycler_accept.format(batch_id=fake_id), headers=headers
        ),
        "recycler-reject": lambda: client.post(
            paths.recycler_reject.format(batch_id=fake_id),
            headers=headers,
            json=json_body or {"note": "QA reject"},
        ),
        "recycler-process": lambda: client.post(
            paths.recycler_process.format(batch_id=fake_id), headers=headers
        ),
        "recycler-notifications": lambda: client.get(paths.recycler_notifications, headers=headers),
        "recycler-mark-read": lambda: client.patch(
            paths.recycler_mark_read.format(notification_id=fake_id), headers=headers
        ),
        "recycler-mark-all-read": lambda: client.patch(
            paths.recycler_mark_all_read, headers=headers
        ),
    }
    return dispatch[endpoint]()


# ---------------------------------------------------------------------------
# RCY-01 | Route contract — all recycler and manager batch routes exist
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_runtime_exposes_manager_batch_routes(app_test):
    """RCY-01a | Manager batch routes exist at runtime."""
    registered = set(app_test.openapi()["paths"].keys())
    expected = {
        "/api/v1/manager/batches",
        "/api/v1/manager/recyclers",
        "/api/v1/manager/batches/{batch_id}/assign",
    }
    missing = expected - registered
    assert not missing, f"Missing manager batch routes: {missing}"


@pytest.mark.api
def test_runtime_exposes_recycler_routes(app_test):
    """RCY-01b | Recycler routes exist at runtime."""
    registered = set(app_test.openapi()["paths"].keys())
    expected = {
        "/api/v1/recycler/batches",
        "/api/v1/recycler/batches/{batch_id}/accept",
        "/api/v1/recycler/batches/{batch_id}/reject",
        "/api/v1/recycler/batches/{batch_id}/process",
        "/api/v1/recycler/notifications",
        "/api/v1/recycler/notifications/{notification_id}/read",
        "/api/v1/recycler/notifications/read",
    }
    missing = expected - registered
    assert not missing, f"Missing recycler routes: {missing}"


# ---------------------------------------------------------------------------
# RCY-02 | 401 / 403 on missing credentials
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize("endpoint", ALL_ENDPOINTS)
def test_missing_credentials_returns_401_or_403(db_client, recycler_paths, endpoint):
    """RCY-02 | Missing credentials → 401 or 403."""
    response = _endpoint_request(db_client, recycler_paths, endpoint)
    assert response.status_code in {
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    }, f"Expected 401/403, got {response.status_code}"


# ---------------------------------------------------------------------------
# RCY-03 | Role enforcement
# ---------------------------------------------------------------------------

NON_MANAGER_ROLES = [Role.CITIZEN, Role.COLLECTION_WORKER, Role.RECYCLER]
NON_RECYCLER_ROLES = [Role.CITIZEN, Role.COLLECTION_WORKER, Role.MUNICIPAL_OFFICER]


@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize("endpoint", MANAGER_ENDPOINTS)
@pytest.mark.parametrize("role", NON_MANAGER_ROLES)
def test_non_manager_cannot_access_manager_batch_endpoints(
    db_client, recycler_paths, make_user, test_zone, bearer_for, endpoint, role
):
    """RCY-03a | Non-manager roles are rejected from manager batch routes."""
    user = make_user(role=role, zone=test_zone)
    response = _endpoint_request(db_client, recycler_paths, endpoint, headers=bearer_for(user))
    assert response.status_code == status.HTTP_403_FORBIDDEN, (
        f"{role.value} should not access {endpoint}, got {response.status_code}"
    )


@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize("endpoint", RECYCLER_ENDPOINTS)
@pytest.mark.parametrize("role", NON_RECYCLER_ROLES)
def test_non_recycler_cannot_access_recycler_endpoints(
    db_client, recycler_paths, make_user, test_zone, bearer_for, endpoint, role
):
    """RCY-03b | Non-recycler roles are rejected from recycler routes."""
    user = make_user(role=role, zone=test_zone)
    response = _endpoint_request(db_client, recycler_paths, endpoint, headers=bearer_for(user))
    assert response.status_code == status.HTTP_403_FORBIDDEN, (
        f"{role.value} should not access {endpoint}, got {response.status_code}"
    )
