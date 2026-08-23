"""Lifecycle, validation, audit and transaction tests for manager writes."""

from __future__ import annotations

import pytest
from fastapi import status
from sqlalchemy import select

from app.features.manager import router as manager_router
from app.features.notifications.models import Notification
from app.models.audit import AuditLog
from app.models.enums import BulkRequestStatus, Role, TicketStatus, UserStatus


@pytest.mark.api
@pytest.mark.integration
def test_manager_resolves_open_complaint_with_audit_and_citizen_notification(
    db_client,
    db,
    manager_paths,
    manager_user,
    manager_ward,
    resident_user,
    make_ticket,
    bearer_for,
):
    ticket = make_ticket(raised_by=resident_user, zone=manager_ward)

    response = db_client.patch(
        manager_paths.ticket_update.format(ticket_id=ticket.id),
        headers=bearer_for(manager_user),
        json={"status": "RESOLVED", "resolution_notes": "Area cleared and verified."},
    )

    db.refresh(ticket)
    assert response.status_code == status.HTTP_200_OK
    assert ticket.status == TicketStatus.RESOLVED
    assert ticket.resolution_notes == "Area cleared and verified."
    assert ticket.resolved_by_id == manager_user.id
    assert ticket.resolved_at is not None

    audits = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "Ticket",
            AuditLog.entity_id == ticket.id,
        )
    ).all()
    assert len(audits) == 1
    assert audits[0].actor_id == manager_user.id

    notifications = db.scalars(
        select(Notification).where(Notification.user_id == resident_user.id)
    ).all()
    assert any(ticket.ref_code in item.body for item in notifications)


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.boundary
@pytest.mark.parametrize("note", ["", "   "])
def test_resolution_requires_a_nonblank_note_without_mutation(
    db_client,
    db,
    manager_paths,
    manager_user,
    manager_ward,
    resident_user,
    make_ticket,
    bearer_for,
    assert_safe_error,
    note,
):
    ticket = make_ticket(raised_by=resident_user, zone=manager_ward)

    response = db_client.patch(
        manager_paths.ticket_update.format(ticket_id=ticket.id),
        headers=bearer_for(manager_user),
        json={"status": "RESOLVED", "resolution_notes": note},
    )

    db.refresh(ticket)
    assert ticket.status == TicketStatus.OPEN
    assert ticket.resolution_notes is None
    assert_safe_error(response, status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR")


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.parametrize(
    "source_status",
    [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.CLOSED],
)
def test_only_open_complaints_can_be_resolved(
    db_client,
    db,
    manager_paths,
    manager_user,
    manager_ward,
    resident_user,
    make_ticket,
    bearer_for,
    assert_safe_error,
    source_status,
):
    ticket = make_ticket(
        raised_by=resident_user,
        zone=manager_ward,
        status=source_status,
        resolution_notes="Existing resolution" if source_status == TicketStatus.RESOLVED else None,
    )

    response = db_client.patch(
        manager_paths.ticket_update.format(ticket_id=ticket.id),
        headers=bearer_for(manager_user),
        json={"status": "RESOLVED", "resolution_notes": "Must not overwrite state."},
    )

    db.refresh(ticket)
    assert ticket.status == source_status
    assert_safe_error(response, status.HTTP_409_CONFLICT, "CONFLICT")


@pytest.mark.api
@pytest.mark.integration
def test_manager_assigns_pending_pickup_with_notifications_and_audit(
    db_client,
    db,
    manager_paths,
    manager_user,
    manager_ward,
    resident_user,
    worker_user,
    make_bulk_request,
    bearer_for,
):
    request = make_bulk_request(requester=resident_user, zone=manager_ward)

    response = db_client.post(
        manager_paths.bulk_assign.format(request_id=request.id),
        headers=bearer_for(manager_user),
        json={"collector_id": str(worker_user.id)},
    )

    db.refresh(request)
    assert response.status_code == status.HTTP_200_OK
    assert request.status == BulkRequestStatus.ASSIGNED
    assert request.assigned_collector_id == worker_user.id
    assert request.decided_by_id == manager_user.id
    assert request.decided_at is not None

    recipients = set(
        db.scalars(
            select(Notification.user_id).where(
                Notification.user_id.in_([resident_user.id, worker_user.id])
            )
        ).all()
    )
    assert recipients == {resident_user.id, worker_user.id}

    audits = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "BulkPickupRequest",
            AuditLog.entity_id == request.id,
        )
    ).all()
    assert len(audits) == 1
    assert audits[0].actor_id == manager_user.id


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.parametrize("collector_case", ["wrong-role", "disabled", "wrong-ward"])
def test_assignment_rejects_an_ineligible_collector_without_mutation(
    db_client,
    db,
    manager_paths,
    manager_user,
    manager_ward,
    other_ward,
    resident_user,
    make_user,
    make_bulk_request,
    bearer_for,
    assert_safe_error,
    collector_case,
):
    if collector_case == "wrong-role":
        collector = make_user(role=Role.CITIZEN, zone=manager_ward)
    elif collector_case == "disabled":
        collector = make_user(
            role=Role.COLLECTION_WORKER,
            status=UserStatus.DISABLED,
            zone=manager_ward,
        )
    else:
        collector = make_user(role=Role.COLLECTION_WORKER, zone=other_ward)
    request = make_bulk_request(requester=resident_user, zone=manager_ward)

    response = db_client.post(
        manager_paths.bulk_assign.format(request_id=request.id),
        headers=bearer_for(manager_user),
        json={"collector_id": str(collector.id)},
    )

    db.refresh(request)
    assert request.status == BulkRequestStatus.PENDING
    assert request.assigned_collector_id is None
    assert_safe_error(response, status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR")


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.lifecycle
@pytest.mark.parametrize(
    "request_status",
    [BulkRequestStatus.ASSIGNED, BulkRequestStatus.REJECTED, BulkRequestStatus.CANCELLED],
)
def test_only_pending_pickups_can_be_assigned(
    db_client,
    db,
    manager_paths,
    manager_user,
    manager_ward,
    resident_user,
    worker_user,
    make_bulk_request,
    bearer_for,
    assert_safe_error,
    request_status,
):
    request = make_bulk_request(
        requester=resident_user,
        zone=manager_ward,
        status=request_status,
    )

    response = db_client.post(
        manager_paths.bulk_assign.format(request_id=request.id),
        headers=bearer_for(manager_user),
        json={"collector_id": str(worker_user.id)},
    )

    db.refresh(request)
    assert request.status == request_status
    assert_safe_error(response, status.HTTP_409_CONFLICT, "CONFLICT")


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.idempotency
def test_repeated_assignment_does_not_overwrite_the_first_collector(
    db_client,
    db,
    manager_paths,
    manager_user,
    manager_ward,
    resident_user,
    worker_user,
    make_user,
    make_bulk_request,
    bearer_for,
    assert_safe_error,
):
    second_worker = make_user(role=Role.COLLECTION_WORKER, zone=manager_ward)
    request = make_bulk_request(requester=resident_user, zone=manager_ward)
    headers = bearer_for(manager_user)

    first = db_client.post(
        manager_paths.bulk_assign.format(request_id=request.id),
        headers=headers,
        json={"collector_id": str(worker_user.id)},
    )
    second = db_client.post(
        manager_paths.bulk_assign.format(request_id=request.id),
        headers=headers,
        json={"collector_id": str(second_worker.id)},
    )

    db.refresh(request)
    assert first.status_code == status.HTTP_200_OK
    assert request.assigned_collector_id == worker_user.id
    assert_safe_error(second, status.HTTP_409_CONFLICT, "CONFLICT")


@pytest.mark.api
@pytest.mark.integration
def test_worker_contact_update_is_audited_with_the_manager_as_actor(
    db_client,
    db,
    manager_paths,
    manager_user,
    worker_user,
    bearer_for,
):
    response = db_client.patch(
        manager_paths.worker_update.format(worker_id=worker_user.id),
        headers=bearer_for(manager_user),
        json={"name": "Updated Worker", "phone": "+919876540099", "status": "ACTIVE"},
    )

    db.refresh(worker_user)
    assert response.status_code == status.HTTP_200_OK
    assert worker_user.name == "Updated Worker"
    assert worker_user.phone == "+919876540099"
    audits = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "User",
            AuditLog.entity_id == worker_user.id,
            AuditLog.action == "CREW_MEMBER_UPDATED",
        )
    ).all()
    assert len(audits) == 1
    assert audits[0].actor_id == manager_user.id


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.boundary
@pytest.mark.parametrize("field", ["name", "phone"])
def test_worker_update_rejects_blank_text_without_persistence(
    db_client,
    db,
    manager_paths,
    manager_user,
    worker_user,
    bearer_for,
    assert_safe_error,
    field,
):
    original_name = worker_user.name
    original_phone = worker_user.phone
    payload = {"name": "Valid Worker", "phone": "+919876540088", "status": "ACTIVE"}
    payload[field] = "   "

    response = db_client.patch(
        manager_paths.worker_update.format(worker_id=worker_user.id),
        headers=bearer_for(manager_user),
        json=payload,
    )

    db.refresh(worker_user)
    assert worker_user.name == original_name
    assert worker_user.phone == original_phone
    assert_safe_error(response, status.HTTP_422_UNPROCESSABLE_ENTITY, "VALIDATION_ERROR")


@pytest.mark.api
@pytest.mark.integration
def test_worker_update_uses_the_canonical_disabled_status(
    db_client,
    db,
    manager_paths,
    manager_user,
    worker_user,
    bearer_for,
):
    response = db_client.patch(
        manager_paths.worker_update.format(worker_id=worker_user.id),
        headers=bearer_for(manager_user),
        json={
            "name": worker_user.name,
            "phone": worker_user.phone,
            "status": "DISABLED",
        },
    )

    db.refresh(worker_user)
    assert response.status_code == status.HTTP_200_OK
    assert worker_user.status == UserStatus.DISABLED


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.security
def test_disabling_worker_increments_token_version_and_revokes_old_session(
    db_client,
    db,
    manager_paths,
    manager_user,
    worker_user,
    bearer_for,
    assert_safe_error,
):
    old_version = worker_user.token_version
    old_headers = bearer_for(worker_user)

    response = db_client.patch(
        manager_paths.worker_update.format(worker_id=worker_user.id),
        headers=bearer_for(manager_user),
        json={
            "name": worker_user.name,
            "phone": worker_user.phone,
            "status": "INACTIVE",
        },
    )
    old_session = db_client.get(manager_paths.me, headers=old_headers)

    db.refresh(worker_user)
    assert response.status_code == status.HTTP_200_OK
    assert worker_user.status == UserStatus.DISABLED
    assert worker_user.token_version == old_version + 1
    assert_safe_error(old_session, status.HTTP_401_UNAUTHORIZED, "AUTHENTICATION_REQUIRED")


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.lifecycle
def test_worker_with_active_pickup_assignment_cannot_be_deleted(
    db_client,
    db,
    manager_paths,
    manager_user,
    manager_ward,
    resident_user,
    worker_user,
    make_bulk_request,
    bearer_for,
    assert_safe_error,
):
    make_bulk_request(
        requester=resident_user,
        zone=manager_ward,
        status=BulkRequestStatus.ASSIGNED,
        assigned_collector=worker_user,
    )

    response = db_client.delete(
        manager_paths.worker_delete.format(worker_id=worker_user.id),
        headers=bearer_for(manager_user),
    )

    db.refresh(worker_user)
    assert worker_user.deleted_at is None
    assert worker_user.status == UserStatus.ACTIVE
    assert_safe_error(response, status.HTTP_409_CONFLICT, "CONFLICT")


@pytest.mark.api
@pytest.mark.integration
def test_unassigned_worker_delete_is_soft_audited_and_revokes_sessions(
    db_client,
    db,
    manager_paths,
    manager_user,
    worker_user,
    bearer_for,
):
    old_version = worker_user.token_version

    response = db_client.delete(
        manager_paths.worker_delete.format(worker_id=worker_user.id),
        headers=bearer_for(manager_user),
    )

    db.refresh(worker_user)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert worker_user.deleted_at is not None
    assert worker_user.status == UserStatus.DISABLED
    assert worker_user.token_version == old_version + 1
    audits = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "User",
            AuditLog.entity_id == worker_user.id,
            AuditLog.action == "CREW_MEMBER_DELETED",
        )
    ).all()
    assert len(audits) == 1
    assert audits[0].actor_id == manager_user.id


@pytest.mark.api
@pytest.mark.integration
def test_worker_update_rolls_back_when_required_audit_fails(
    db_client_no_raise,
    db,
    monkeypatch,
    manager_paths,
    manager_user,
    worker_user,
    bearer_for,
):
    original_name = worker_user.name
    original_phone = worker_user.phone

    def _fail_audit(*_args, **_kwargs):
        raise RuntimeError("simulated required audit failure")

    monkeypatch.setattr(manager_router, "create_audit_log", _fail_audit)

    response = db_client_no_raise.patch(
        manager_paths.worker_update.format(worker_id=worker_user.id),
        headers=bearer_for(manager_user),
        json={"name": "Must Roll Back", "phone": "+919876540077", "status": "ACTIVE"},
    )

    db.expire_all()
    persisted = db.get(type(worker_user), worker_user.id)
    assert response.status_code >= 500
    assert persisted.name == original_name
    assert persisted.phone == original_phone


@pytest.mark.api
@pytest.mark.integration
@pytest.mark.idempotency
def test_mark_all_notifications_read_is_recipient_scoped_and_repeat_safe(
    db_client,
    db,
    manager_paths,
    manager_user,
    other_ward,
    make_user,
    make_notification,
    bearer_for,
):
    other_manager = make_user(role=Role.MUNICIPAL_OFFICER, zone=other_ward)
    own = [make_notification(user=manager_user) for _ in range(3)]
    foreign = make_notification(user=other_manager)

    first = db_client.patch(
        manager_paths.notifications_read,
        headers=bearer_for(manager_user),
    )
    second = db_client.patch(
        manager_paths.notifications_read,
        headers=bearer_for(manager_user),
    )

    for notification in [*own, foreign]:
        db.refresh(notification)
    assert first.status_code == status.HTTP_200_OK
    assert first.json() == {"marked_read": 3}
    assert second.status_code == status.HTTP_200_OK
    assert second.json() == {"marked_read": 0}
    assert all(item.is_read for item in own)
    assert foreign.is_read is False
