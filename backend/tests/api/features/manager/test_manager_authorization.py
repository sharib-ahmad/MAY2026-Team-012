"""Object and ward authorisation tests for manager operations."""

from __future__ import annotations

import pytest
from fastapi import status

from app.models.enums import Role


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.security
@pytest.mark.parametrize("operation", ["ticket", "bulk"])
def test_manager_without_assigned_wards_is_denied_state_changes(
    db_client,
    db,
    manager_paths,
    manager_without_wards,
    other_ward,
    make_user,
    make_ticket,
    make_bulk_request,
    bearer_for,
    assert_safe_error,
    operation,
):
    resident = make_user(role=Role.CITIZEN, zone=other_ward)
    headers = bearer_for(manager_without_wards)

    if operation == "ticket":
        resource = make_ticket(raised_by=resident, zone=other_ward)
        response = db_client.patch(
            manager_paths.ticket_update.format(ticket_id=resource.id),
            headers=headers,
            json={"status": "RESOLVED", "resolution_notes": "Resolved by QA."},
        )
        db.refresh(resource)
        assert resource.status.value == "OPEN"
        assert resource.resolution_notes is None
    else:
        worker = make_user(role=Role.COLLECTION_WORKER, zone=other_ward)
        resource = make_bulk_request(requester=resident, zone=other_ward)
        response = db_client.post(
            manager_paths.bulk_assign.format(request_id=resource.id),
            headers=headers,
            json={"collector_id": str(worker.id)},
        )
        db.refresh(resource)
        assert resource.status.value == "PENDING"
        assert resource.assigned_collector_id is None

    assert_safe_error(response, status.HTTP_403_FORBIDDEN, "FORBIDDEN")


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.security
@pytest.mark.parametrize(
    "operation",
    ["ticket", "bulk", "worker-update", "worker-delete"],
)
def test_manager_cannot_read_or_mutate_objects_from_another_ward(
    db_client,
    db,
    manager_paths,
    manager_user,
    other_ward,
    make_user,
    make_ticket,
    make_bulk_request,
    bearer_for,
    assert_safe_error,
    operation,
):
    resident = make_user(role=Role.CITIZEN, zone=other_ward)
    worker = make_user(role=Role.COLLECTION_WORKER, zone=other_ward)
    headers = bearer_for(manager_user)

    if operation == "ticket":
        resource = make_ticket(raised_by=resident, zone=other_ward)
        response = db_client.patch(
            manager_paths.ticket_update.format(ticket_id=resource.id),
            headers=headers,
            json={"status": "RESOLVED", "resolution_notes": "Wrong ward."},
        )
        db.refresh(resource)
        assert resource.status.value == "OPEN"
        assert resource.resolution_notes is None
    elif operation == "bulk":
        resource = make_bulk_request(requester=resident, zone=other_ward)
        response = db_client.post(
            manager_paths.bulk_assign.format(request_id=resource.id),
            headers=headers,
            json={"collector_id": str(worker.id)},
        )
        db.refresh(resource)
        assert resource.status.value == "PENDING"
        assert resource.assigned_collector_id is None
    elif operation == "worker-update":
        original_name = worker.name
        response = db_client.patch(
            manager_paths.worker_update.format(worker_id=worker.id),
            headers=headers,
            json={"name": "Foreign Worker", "phone": worker.phone, "status": "ACTIVE"},
        )
        db.refresh(worker)
        assert worker.name == original_name
    else:
        response = db_client.delete(
            manager_paths.worker_delete.format(worker_id=worker.id),
            headers=headers,
        )
        db.refresh(worker)
        assert worker.deleted_at is None

    assert_safe_error(response, status.HTTP_403_FORBIDDEN, "FORBIDDEN")
