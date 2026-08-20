"""Manager dashboard scoping, privacy and scale tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status

from app.core.config import get_settings
from app.models.enums import Role, TicketStatus


@pytest.mark.api
@pytest.mark.integration
def test_dashboard_contains_only_the_managers_assigned_wards(
    db_client,
    manager_paths,
    manager_user,
    manager_ward,
    other_ward,
    make_user,
    make_ticket,
    make_bulk_request,
    bearer_for,
):
    own_resident = make_user(role=Role.CITIZEN, zone=manager_ward)
    foreign_resident = make_user(role=Role.CITIZEN, zone=other_ward)
    make_user(role=Role.COLLECTION_WORKER, zone=manager_ward)
    make_user(role=Role.COLLECTION_WORKER, zone=other_ward)
    own_ticket = make_ticket(raised_by=own_resident, zone=manager_ward)
    make_ticket(raised_by=foreign_resident, zone=other_ward)
    make_bulk_request(requester=own_resident, zone=manager_ward)
    make_bulk_request(requester=foreign_resident, zone=other_ward)

    response = db_client.get(manager_paths.dashboard, headers=bearer_for(manager_user))

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    # Bulk-pickup and crew sections are operational queues the manager acts on:
    # they stay strictly scoped to the manager's own assigned wards.
    assert all(item["ward_code"] == manager_ward.code for item in body["bulk_pickups"])
    assert all(item["ward_code"] == manager_ward.code for item in body["workers"])
    # Complaint dashboard reads are city-wide by design so an officer can spot
    # service gaps outside their own wards (Story 2.2); only complaint
    # *mutation* is ward-scoped (covered in test_manager_authorization.py).
    # `ward_coverage` is explicitly every ward in the system, flagged by
    # `is_managed`, and `all_ward_open_complaints` is an every-ward complaint
    # count for the same reason — neither is a leak.
    ward_coverage_codes = {item["code"]: item["is_managed"] for item in body["ward_coverage"]}
    assert ward_coverage_codes[manager_ward.code] is True
    assert ward_coverage_codes[other_ward.code] is False
    assert other_ward.code in {row["ward"] for row in body["all_ward_open_complaints"]}
    assert {item["id"] for item in body["complaints"]} == {str(own_ticket.id)}


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.security
def test_manager_without_wards_gets_an_empty_scoped_dashboard(
    db_client,
    manager_paths,
    manager_without_wards,
    other_ward,
    make_user,
    make_ticket,
    bearer_for,
):
    resident = make_user(role=Role.CITIZEN, zone=other_ward)
    make_ticket(raised_by=resident, zone=other_ward)

    response = db_client.get(
        manager_paths.dashboard,
        headers=bearer_for(manager_without_wards),
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    for key in (
        "wards",
        "complaints",
        "routes",
        "delay_logs",
        "mixed_waste_flags",
        "bulk_pickups",
        "workers",
    ):
        assert body[key] == []
    assert body["stats"]["open_complaints"] == 0
    assert body["stats"]["wards_supervised"] == 0
    # ward_coverage and all_ward_open_complaints are explicitly every-ward,
    # city-wide views (not scoped to the officer's own assignment), so an
    # officer with zero assigned wards still sees them populated.
    assert other_ward.code in {item["code"] for item in body["ward_coverage"]}
    assert all(item["is_managed"] is False for item in body["ward_coverage"])
    assert other_ward.code in {row["ward"] for row in body["all_ward_open_complaints"]}


@pytest.mark.api
@pytest.mark.integration
def test_dashboard_complaints_are_bounded_and_stably_ordered(
    db_client,
    manager_paths,
    manager_user,
    manager_ward,
    make_user,
    make_ticket,
    bearer_for,
):
    resident = make_user(role=Role.CITIZEN, zone=manager_ward)
    for index in range(25):
        make_ticket(
            raised_by=resident,
            zone=manager_ward,
            description=f"QA complaint {index:02d}",
            created_at=datetime.now(UTC) - timedelta(minutes=index),
        )

    response = db_client.get(manager_paths.dashboard, headers=bearer_for(manager_user))

    assert response.status_code == status.HTTP_200_OK
    complaints = response.json()["complaints"]
    assert len(complaints) <= 20
    created = [item["created_at"] for item in complaints]
    assert created == sorted(created, reverse=True)


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.boundary
def test_dashboard_marks_complaints_at_the_aging_threshold(
    db_client,
    manager_paths,
    manager_user,
    manager_ward,
    make_user,
    make_ticket,
    bearer_for,
):
    resident = make_user(role=Role.CITIZEN, zone=manager_ward)
    threshold = get_settings().COMPLAINT_AGING_THRESHOLD_DAYS
    now = datetime.now(UTC)
    recent = make_ticket(
        raised_by=resident,
        zone=manager_ward,
        created_at=now - timedelta(days=threshold) + timedelta(seconds=1),
    )
    aging = make_ticket(
        raised_by=resident,
        zone=manager_ward,
        created_at=now - timedelta(days=threshold),
    )
    resolved = make_ticket(
        raised_by=resident,
        zone=manager_ward,
        status=TicketStatus.RESOLVED,
        created_at=now - timedelta(days=threshold + 1),
    )

    response = db_client.get(manager_paths.dashboard, headers=bearer_for(manager_user))

    assert response.status_code == status.HTTP_200_OK
    rows = {item["id"]: item for item in response.json()["complaints"]}
    assert rows[str(recent.id)]["is_aging"] is False
    assert rows[str(aging.id)]["is_aging"] is True
    assert rows[str(resolved.id)]["is_aging"] is False


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.security
def test_dashboard_limits_own_notifications_and_hides_internal_fields(
    db_client,
    manager_paths,
    manager_user,
    other_ward,
    make_user,
    make_notification,
    bearer_for,
    assert_safe_public_body,
):
    other_user = make_user(role=Role.MUNICIPAL_OFFICER, zone=other_ward)
    for index in range(12):
        make_notification(user=manager_user, title=f"Own {index:02d}")
    make_notification(user=other_user, title="Foreign notification")

    response = db_client.get(manager_paths.dashboard, headers=bearer_for(manager_user))

    assert response.status_code == status.HTTP_200_OK
    notifications = response.json()["notifications"]
    assert len(notifications) == 10
    assert all(item["title"].startswith("Own") for item in notifications)
    assert_safe_public_body(response)
