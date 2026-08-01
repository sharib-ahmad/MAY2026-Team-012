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
def test_public_wards_use_canonical_route_schema_and_order(
    db_client,
    db,
    admin_paths,
    assert_safe_public_body,
):
    db.add_all(
        [
            Zone(code="W-09", name="Ward Nine", sectors="Sector 9"),
            Zone(code="W-02", name="Ward Two", sectors=None),
        ]
    )
    db.flush()

    response = db_client.get("/api/v1/wards")

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert isinstance(body, list)
    assert [item["code"] for item in body] == sorted(item["code"] for item in body)
    for item in body:
        assert {"id", "code", "name", "sectors"} <= set(item)
        assert "manager_id" not in item
    assert_safe_public_body(response)


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
            "code": f" {code.lower()} ",
            "name": "  QA Ward  ",
            "sectors": " Sector A ",
        },
    )
    assert created.status_code == status.HTTP_201_CREATED
    created_body = created.json()
    ward_id = created_body["id"]
    assert created_body["code"] == code
    assert created_body["name"] == "QA Ward"

    listing = db_client.get(admin_paths.ward_collection, headers=headers)
    assert listing.status_code == status.HTTP_200_OK
    list_body = listing.json()
    items = list_body["items"] if "items" in list_body else list_body.get("wards", [])
    assert any(str(item["id"]) == str(ward_id) for item in items)

    updated = db_client.patch(
        admin_paths.ward_item.format(ward_id=ward_id),
        headers=headers,
        json={"name": "QA Ward Renamed", "sectors": None},
    )
    assert updated.status_code == status.HTTP_200_OK
    assert updated.json()["name"] == "QA Ward Renamed"
    assert updated.json()["sectors"] is None

    audits_before_delete = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "Zone",
            AuditLog.entity_id == uuid.UUID(str(ward_id)),
        )
    ).all()
    assert len(audits_before_delete) >= 2
    assert {audit.actor_id for audit in audits_before_delete} == {admin_user.id}

    deleted = db_client.delete(
        admin_paths.ward_item.format(ward_id=ward_id),
        headers=headers,
    )
    assert deleted.status_code == status.HTTP_204_NO_CONTENT
    assert db.get(Zone, uuid.UUID(str(ward_id))) is None
    assert_safe_public_body(listing)


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
    assert_safe_error(duplicate, status.HTTP_409_CONFLICT, "DUPLICATE_RESOURCE")

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
    assert_safe_error(response, status.HTTP_409_CONFLICT, "CONFLICT")


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.security
def test_dashboard_and_logs_are_admin_only_bounded_and_do_not_leak_internal_fields(
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

    dashboard_text = dashboard.text.lower()
    assert "password_hash" not in dashboard_text
    assert "token_version" not in dashboard_text
    assert "deleted_at" not in dashboard_text
    assert "zone_id" not in dashboard_text

    logs_body = logs.json()
    items = logs_body["items"] if "items" in logs_body else logs_body.get("logs", [])
    assert len(items) <= 20
    timestamps = [item.get("created_at", item.get("timestamp")) for item in items]
    assert timestamps == sorted(timestamps, reverse=True)
    assert_safe_public_body(dashboard)
    assert_safe_public_body(logs)
