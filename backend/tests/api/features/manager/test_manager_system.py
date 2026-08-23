"""One high-value manager cross-feature system journey."""

from __future__ import annotations

import pytest
from fastapi import status
from sqlalchemy import select

from app.features.notifications.models import Notification
from app.models.audit import AuditLog
from app.models.enums import BulkRequestStatus, Role, TicketStatus


@pytest.mark.system
@pytest.mark.integration
def test_manager_dashboard_resolution_and_assignment_journey(
    db_client,
    db,
    manager_paths,
    manager_user,
    manager_ward,
    other_ward,
    resident_user,
    worker_user,
    make_user,
    make_ticket,
    make_bulk_request,
    bearer_for,
    assert_safe_error,
):
    ticket = make_ticket(raised_by=resident_user, zone=manager_ward)
    pickup = make_bulk_request(requester=resident_user, zone=manager_ward)
    foreign_resident = make_user(role=Role.CITIZEN, zone=other_ward)
    foreign_ticket = make_ticket(raised_by=foreign_resident, zone=other_ward)
    headers = bearer_for(manager_user)

    dashboard = db_client.get(manager_paths.dashboard, headers=headers)
    assert dashboard.status_code == status.HTTP_200_OK
    body = dashboard.json()
    assert str(ticket.id) in {item["id"] for item in body["complaints"]}
    assert str(pickup.id) in {item["id"] for item in body["bulk_pickups"]}

    resolved = db_client.patch(
        manager_paths.ticket_update.format(ticket_id=ticket.id),
        headers=headers,
        json={"status": "RESOLVED", "resolution_notes": "Completed in system journey."},
    )
    assigned = db_client.post(
        manager_paths.bulk_assign.format(request_id=pickup.id),
        headers=headers,
        json={"collector_id": str(worker_user.id)},
    )
    denied = db_client.patch(
        manager_paths.ticket_update.format(ticket_id=foreign_ticket.id),
        headers=headers,
        json={"status": "RESOLVED", "resolution_notes": "Cross-ward attempt."},
    )

    db.refresh(ticket)
    db.refresh(pickup)
    assert resolved.status_code == status.HTTP_200_OK
    assert assigned.status_code == status.HTTP_200_OK
    assert ticket.status == TicketStatus.RESOLVED
    assert pickup.status == BulkRequestStatus.ASSIGNED
    assert pickup.assigned_collector_id == worker_user.id
    assert_safe_error(denied, status.HTTP_403_FORBIDDEN, "FORBIDDEN")

    audit_actions = set(
        db.scalars(select(AuditLog.action).where(AuditLog.actor_id == manager_user.id)).all()
    )
    assert "BULK_PICKUP_ASSIGNED" in audit_actions

    # R2/Story 2.3 AC4 require an audit row with actor and timestamp for the
    # status change; no accepted contract names a resolution-specific action
    # string, so only entity/actor/timestamp are asserted here.
    ticket_audits = db.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "Ticket",
            AuditLog.entity_id == ticket.id,
        )
    ).all()
    assert len(ticket_audits) == 1
    assert ticket_audits[0].actor_id == manager_user.id
    assert ticket_audits[0].created_at is not None

    recipients = set(
        db.scalars(
            select(Notification.user_id).where(
                Notification.user_id.in_([resident_user.id, worker_user.id])
            )
        ).all()
    )
    assert recipients == {resident_user.id, worker_user.id}
