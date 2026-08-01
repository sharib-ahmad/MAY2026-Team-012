"""Contract and access-control tests for the Citizen / Resident API (SCRUM-97)."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status


@pytest.mark.api
def test_runtime_exposes_the_approved_citizen_contract(app_test):
    """Verify runtime exposes the approved canonical citizen endpoints."""
    routes = {
        (method, route.path)
        for route in app_test.routes
        for method in getattr(route, "methods", set())
    }

    required = {
        ("POST", "/api/v1/user/pickups"),
        ("GET", "/api/v1/user/pickups"),
        ("PATCH", "/api/v1/user/pickups/{pickup_id}/cancel"),
        ("GET", "/api/v1/user/pickups/{pickup_id}/tracking"),
        ("GET", "/api/v1/user/pickup-options"),
        ("POST", "/api/v1/user/tickets"),
        ("GET", "/api/v1/user/tickets"),
        ("GET", "/api/v1/user/notifications"),
        ("PATCH", "/api/v1/user/notifications/{notification_id}/read"),
        ("GET", "/api/v1/user/dashboard"),
        ("GET", "/api/v1/user/impact"),
        ("GET", "/api/v1/user/daily-pickup-schedules"),
    }

    assert required <= routes


def _endpoint_request(client, paths, key, headers=None):
    pickup_id = uuid.uuid4()
    notif_id = uuid.uuid4()
    headers = headers or {}

    if key == "dashboard":
        return client.get(paths.dashboard, headers=headers)
    if key == "impact":
        return client.get(paths.impact, headers=headers)
    if key == "list-pickups":
        return client.get(paths.pickups, headers=headers)
    if key == "create-pickup":
        return client.post(
            paths.pickups,
            headers=headers,
            json={
                "category": "PLASTIC",
                "estimated_weight": 5.0,
                "scheduled_date": "2026-08-05T10:00:00Z",
                "time_slot": "Morning (8-11)",
            },
        )
    if key == "cancel-pickup":
        return client.patch(
            paths.cancel_pickup.format(pickup_id=pickup_id),
            headers=headers,
        )
    if key == "tracking":
        return client.get(
            paths.tracking.format(pickup_id=pickup_id),
            headers=headers,
        )
    if key == "pickup-options":
        return client.get(paths.pickup_options, headers=headers)
    if key == "list-tickets":
        return client.get(paths.complaints, headers=headers)
    if key == "create-ticket":
        return client.post(
            paths.complaints,
            headers=headers,
            json={
                "issue_type": "MISSED_PICKUP",
                "description": "Valid complaint description text for access testing.",
            },
        )
    if key == "notifications":
        return client.get(paths.notifications, headers=headers)
    if key == "mark-notification":
        return client.patch(
            paths.mark_notification.format(notification_id=notif_id),
            headers=headers,
        )
    if key == "daily-schedules":
        return client.get(paths.daily_schedules, headers=headers)
    raise AssertionError(f"Unknown endpoint key: {key}")


@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize(
    "endpoint_key",
    [
        "dashboard",
        "impact",
        "list-pickups",
        "create-pickup",
        "cancel-pickup",
        "tracking",
        "pickup-options",
        "list-tickets",
        "create-ticket",
        "notifications",
        "mark-notification",
        "daily-schedules",
    ],
)
def test_every_citizen_endpoint_rejects_missing_credentials(
    db_client,
    citizen_paths,
    endpoint_key,
    assert_safe_public_body,
):
    """Verify missing credentials return 401 or 403 status across citizen endpoints."""
    response = _endpoint_request(db_client, citizen_paths, endpoint_key)
    assert response.status_code in {status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN}
    assert_safe_public_body(response)


@pytest.mark.api
@pytest.mark.security
@pytest.mark.parametrize(
    "endpoint_key",
    [
        "dashboard",
        "impact",
        "list-pickups",
        "create-pickup",
        "cancel-pickup",
        "tracking",
        "pickup-options",
        "list-tickets",
        "create-ticket",
        "notifications",
        "mark-notification",
        "daily-schedules",
    ],
)
def test_every_citizen_endpoint_rejects_non_citizen_roles(
    db_client,
    citizen_paths,
    officer_user,
    bearer_for,
    endpoint_key,
    assert_safe_error,
):
    """Verify non-citizen roles (e.g. Officer) receive 403 Forbidden across all endpoints."""
    response = _endpoint_request(
        db_client,
        citizen_paths,
        endpoint_key,
        headers=bearer_for(officer_user),
    )
    assert_safe_error(response, status.HTTP_403_FORBIDDEN)
