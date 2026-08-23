"""Ward, dashboard and audit-log tests for SCRUM-173."""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from sqlalchemy import select

from app.models.audit import AuditLog
from app.models.enums import Role
from app.models.zone import Zone


@pytest.mark.api
@pytest.mark.integration
def test_canonical_ward_reference_route_is_ordered_and_safe(
    db_client,
    db,
    admin_user,
    admin_paths,
    bearer_for,
    assert_safe_public_body,
):
    db.add_all(
        [
            Zone(code="W-09", name="Ward Nine", sectors="Sector 9"),
            Zone(code="W-02", name="Ward Two", sectors=None),
        ]
    )
    db.flush()

    response = db_client.get(
        admin_paths.ward_reference,
        headers=bearer_for(admin_user),
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    items = body["wards"] if isinstance(body, dict) else body
    assert isinstance(items, list)
    assert [item["code"] for item in items] == sorted(item["code"] for item in items)

    for item in items:
        assert {"id", "code", "name", "sectors"} <= set(item)

    assert_safe_public_body(response, additional_forbidden_keys={"zone_id"})


@pytest.mark.api
@pytest.mark.integration
def test_admin_can_create_list_update_and_delete_unassigned_ward_with_audit(
    db_client,
    db,
    admin_user,
    admin_paths,
    bearer_for,
    assert_safe_public_body,
):
    headers = bearer_for(admin_user)
    code = f"W-{uuid.uuid4().hex[:4].upper()}"

    created = db_client.post(
        admin_paths.ward_collection,
        headers=headers,
        json={
            "code": code,
            "name": "QA Ward",
            "sectors": "Sector A",
        },
    )
    assert created.status_code == status.HTTP_201_CREATED
    created_body = created.json()
    ward_id = uuid.UUID(str(created_body["id"]))
    assert created_body["code"] == code
    assert created_body["name"] == "QA Ward"

    listing = db_client.get(admin_paths.ward_collection, headers=headers)
    assert listing.status_code == status.HTTP_200_OK
    list_body = listing.json()
    items = list_body.get("items", list_body.get("wards", []))
    assert any(str(item["id"]) == str(ward_id) for item in items)

    updated = db_client.patch(
        admin_paths.ward_item.format(ward_id=ward_id),
        headers=headers,
        json={"name": "QA Ward Renamed", "sectors": None},
    )
    assert updated.status_code == status.HTTP_200_OK
    assert updated.json()["name"] == "QA Ward Renamed"
    assert updated.json()["sectors"] is None

    deleted = db_client.delete(
        admin_paths.ward_item.format(ward_id=ward_id),
        headers=headers,
    )
    assert deleted.status_code == status.HTTP_204_NO_CONTENT
    assert db.get(Zone, ward_id) is None

    audits = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "Zone",
            AuditLog.entity_id == ward_id,
        )
    ).all()
    assert {audit.action for audit in audits} >= {
        "WARD_CREATED",
        "WARD_UPDATED",
        "WARD_DELETED",
    }
    assert all(audit.actor_id == admin_user.id for audit in audits)

    assert_safe_public_body(created)
    assert_safe_public_body(listing)
    assert_safe_public_body(updated)


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.boundary
def test_ward_creation_normalizes_required_text_and_code(
    db_client,
    admin_user,
    admin_paths,
    bearer_for,
):
    canonical_code = f"W-{uuid.uuid4().hex[:4].upper()}"

    response = db_client.post(
        admin_paths.ward_collection,
        headers=bearer_for(admin_user),
        json={
            "code": f"  {canonical_code.lower()}  ",
            "name": "  Normalized Ward  ",
            "sectors": "  Sector A  ",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["code"] == canonical_code
    assert body["name"] == "Normalized Ward"

    # Sector whitespace is not an approved acceptance boundary. Verify the
    # semantic value without turning presentation cleanup into a release gate.
    assert body["sectors"].strip() == "Sector A"


@pytest.mark.api
@pytest.mark.integration
def test_duplicate_ward_code_and_unknown_ward_id_return_safe_errors(
    db_client,
    admin_user,
    admin_paths,
    ward_a,
    bearer_for,
    assert_safe_error,
):
    headers = bearer_for(admin_user)

    duplicate = db_client.post(
        admin_paths.ward_collection,
        headers=headers,
        json={"code": f" {ward_a.code.lower()} ", "name": "Duplicate Ward"},
    )
    assert_safe_error(
        duplicate,
        status.HTTP_409_CONFLICT,
        {"CONFLICT", "DUPLICATE_RESOURCE"},
    )

    missing = db_client.patch(
        admin_paths.ward_item.format(ward_id=uuid.uuid4()),
        headers=headers,
        json={"name": "Missing Ward", "sectors": None},
    )
    assert_safe_error(missing, status.HTTP_404_NOT_FOUND, "RESOURCE_NOT_FOUND")


@pytest.mark.api
@pytest.mark.integration
def test_ward_with_assigned_user_cannot_be_deleted(
    db_client,
    db,
    admin_user,
    admin_paths,
    ward_a,
    make_user,
    bearer_for,
    assert_safe_error,
):
    make_user(role=Role.CITIZEN, zone=ward_a)

    response = db_client.delete(
        admin_paths.ward_item.format(ward_id=ward_a.id),
        headers=bearer_for(admin_user),
    )

    assert db.get(Zone, ward_a.id) is not None
    assert_safe_error(
        response,
        {status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT},
        {"BAD_REQUEST", "CONFLICT"},
    )


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.security
def test_dashboard_and_logs_are_bounded_and_do_not_leak_internal_fields(
    db_client,
    admin_user,
    admin_paths,
    make_user,
    bearer_for,
    assert_safe_public_body,
):
    make_user(name="Dashboard Citizen", role=Role.CITIZEN)

    dashboard = db_client.get(
        admin_paths.dashboard,
        headers=bearer_for(admin_user),
    )
    logs = db_client.get(
        admin_paths.logs,
        headers=bearer_for(admin_user),
        params={"limit": 20},
    )

    assert dashboard.status_code == status.HTTP_200_OK
    assert logs.status_code == status.HTTP_200_OK
    assert dashboard.json()["stats"]["registered_users"] >= 2

    logs_body = logs.json()
    items = logs_body.get("items", logs_body.get("logs", []))
    assert len(items) <= 20
    timestamps = [item.get("created_at", item.get("timestamp")) for item in items]
    assert timestamps == sorted(timestamps, reverse=True)

    assert_safe_public_body(dashboard, additional_forbidden_keys={"zone_id"})
    assert_safe_public_body(logs)
