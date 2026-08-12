from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.bulk_pickups.models import BulkPickupRequest
from app.features.complaints.models import Ticket
from app.features.manager.dependencies import require_manager
from app.features.manager.schemas import BulkPickupAssignment, TicketUpdate, WorkerUpdate
from app.features.manager.service import get_dashboard_data, get_managed_zone_ids
from app.features.notifications.models import Notification
from app.features.users.models import User
from app.models.audit import create_audit_log
from app.models.enums import BulkRequestStatus, Role, TicketStatus, UserStatus

router = APIRouter(prefix="/manager", tags=["Manager"])

# Handle Starlette version differences for HTTP status codes
try:
    HTTP_422 = status.HTTP_422_UNPROCESSABLE_CONTENT
except AttributeError:
    HTTP_422 = status.HTTP_422_UNPROCESSABLE_ENTITY


@router.get("/dashboard")
def get_manager_dashboard(
    current_user: User = Depends(require_manager), db: Session = Depends(get_db)
) -> dict:
    """Return the authenticated manager's live ward operations dashboard."""
    return get_dashboard_data(db, current_user)


@router.patch("/notifications/read")
def mark_manager_notifications_read(
    current_user: User = Depends(require_manager), db: Session = Depends(get_db)
) -> dict:
    """Mark every unread notification for the current manager as read."""
    result = db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
    return {"marked_read": result.rowcount}


@router.patch("/tickets/{ticket_id}")
def update_manager_ticket(
    ticket_id: UUID,
    payload: TicketUpdate,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> dict:
    """Update a ticket in the manager's wards and persist the resolution."""
    ticket = db.scalar(select(Ticket).where(Ticket.id == ticket_id))
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    managed_ids = get_managed_zone_ids(db, current_user)
    if managed_ids and ticket.zone_id not in managed_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Complaint is outside your wards."
        )
    if payload.status == TicketStatus.RESOLVED and not (payload.resolution_notes or "").strip():
        raise HTTPException(
            status_code=HTTP_422,
            detail="A resolution note is required to resolve a complaint.",
        )

    previous_status = ticket.status
    ticket.status = payload.status
    ticket.resolution_notes = (payload.resolution_notes or "").strip() or None
    if payload.status == TicketStatus.RESOLVED:
        ticket.resolved_at = datetime.now(UTC)
        ticket.resolved_by_id = current_user.id
    else:
        ticket.resolved_at = None
        ticket.resolved_by_id = None
    if previous_status != ticket.status:
        note_suffix = f" Note: {ticket.resolution_notes}" if ticket.resolution_notes else ""
        db.add(
            Notification(
                user_id=ticket.raised_by_id,
                title="Complaint status updated",
                body=(
                    f"Your complaint {ticket.ref_code} is now "
                    f"{ticket.status.value.replace('_', ' ').lower()}.{note_suffix}"
                ),
            )
        )
    db.flush()
    create_audit_log(
        db,
        actor_id=str(current_user.id),
        actor_name=current_user.name,
        actor_role=current_user.role.value,
        action="COMPLAINT_STATUS_CHANGED",
        entity_type="Ticket",
        entity_id=str(ticket.id),
        module="manager",
        description=(
            f"Complaint {ticket.ref_code} status changed from "
            f"{previous_status.value} to {ticket.status.value}"
            + (f"; note: {ticket.resolution_notes}" if ticket.resolution_notes else "")
        ),
        commit=False,
        required=True,
    )
    db.commit()
    return {"id": str(ticket.id), "status": ticket.status.value}


@router.post("/bulk-pickups/{request_id}/assign")
def assign_bulk_pickup(
    request_id: UUID,
    payload: BulkPickupAssignment,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> dict:
    """Assign a bulk pickup only to an active collector from the request's ward."""
    request = db.scalar(select(BulkPickupRequest).where(BulkPickupRequest.id == request_id))
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bulk pickup request not found."
        )
    managed_ids = get_managed_zone_ids(db, current_user)
    if managed_ids and request.zone_id not in managed_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Pickup is outside your wards."
        )
    collector = db.scalar(
        select(User).where(
            User.id == payload.collector_id,
            User.role == Role.COLLECTION_WORKER,
            User.status == UserStatus.ACTIVE,
            User.deleted_at.is_(None),
            User.zone_id == request.zone_id,
        )
    )
    if not collector:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Choose an active collector from the same ward as the pickup.",
        )
    request.assigned_collector_id = collector.id
    request.decided_by_id = current_user.id
    request.decided_at = datetime.now(UTC)
    request.status = BulkRequestStatus.ASSIGNED

    db.add_all(
        [
            Notification(
                user_id=request.requester_id,
                title="Bulk pickup assigned",
                body=f"{request.ref_code} has been assigned to {collector.name}.",
            ),
            Notification(
                user_id=collector.id,
                title="New bulk pickup assignment",
                body=f"You were assigned {request.ref_code} in your ward.",
            ),
        ]
    )
    db.flush()
    create_audit_log(
        db,
        actor_id=str(current_user.id),
        actor_name=current_user.name,
        actor_role=current_user.role.value,
        action="BULK_PICKUP_ASSIGNED",
        entity_type="BulkPickupRequest",
        entity_id=str(request.id),
        module="manager",
        description=(
            f"Bulk pickup {request.ref_code} assigned to collector "
            f"{collector.name} ({collector.id}) by manager {current_user.name}"
        ),
        commit=False,
        required=True,
    )
    db.commit()
    return {"id": str(request.id), "status": request.status.value, "collector_name": collector.name}


@router.patch("/workers/{worker_id}")
def update_worker(
    worker_id: UUID,
    payload: WorkerUpdate,
    request: Request,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> dict:
    """Edit a collector's contact details or active state within the manager's wards."""
    worker = db.scalar(select(User).where(User.id == worker_id, User.deleted_at.is_(None)))
    if not worker or worker.role != Role.COLLECTION_WORKER:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew member not found.")
    if worker.zone_id not in get_managed_zone_ids(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Collector is outside your wards."
        )
    old_values = {"name": worker.name, "phone": worker.phone, "status": worker.status.value}
    new_status = UserStatus.ACTIVE if payload.status == "ACTIVE" else UserStatus.DISABLED
    worker.name = payload.name.strip()
    worker.phone = payload.phone.strip()
    worker.status = new_status
    # Revoke existing sessions when disabling a worker
    if new_status == UserStatus.DISABLED:
        worker.token_version += 1
    create_audit_log(
        db,
        actor_id=str(current_user.id),
        actor_name=current_user.name,
        actor_role=current_user.role.value,
        action="CREW_MEMBER_UPDATED",
        entity_type="User",
        entity_id=str(worker.id),
        module="manager",
        description=(
            f"Manager updated {worker.role.value} {worker.name}: "
            f"name {old_values['name']!r} → {worker.name!r}, "
            f"phone {old_values['phone']!r} → {worker.phone!r}, "
            f"status {old_values['status']} → {payload.status}"
        ),
        ip_address=request.client.host if request.client else None,
        commit=False,
        required=True,
    )
    db.commit()
    return {
        "id": str(worker.id),
        "name": worker.name,
        "phone": worker.phone,
        "status": payload.status,
    }


@router.delete("/workers/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_worker(
    worker_id: UUID,
    request: Request,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> None:
    """Soft-delete a collector within the manager's wards."""
    worker = db.scalar(select(User).where(User.id == worker_id, User.deleted_at.is_(None)))
    if not worker or worker.role != Role.COLLECTION_WORKER:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Crew member not found.")
    if worker.zone_id not in get_managed_zone_ids(db, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Collector is outside your wards."
        )
    worker_name = worker.name
    worker_role = worker.role.value
    worker_uuid = worker.id

    # Block deletion if worker has an active bulk pickup assignment
    active_assignment = db.scalar(
        select(BulkPickupRequest).where(
            BulkPickupRequest.assigned_collector_id == worker.id,
            BulkPickupRequest.status.in_([BulkRequestStatus.PENDING, BulkRequestStatus.ASSIGNED]),
        )
    )
    if active_assignment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a collector with an active pickup assignment.",
        )

    worker.deleted_at = datetime.now(UTC)
    worker.status = UserStatus.DISABLED
    worker.token_version += 1  # revoke existing sessions immediately
    create_audit_log(
        db,
        actor_id=str(current_user.id),
        actor_name=current_user.name,
        actor_role=current_user.role.value,
        action="CREW_MEMBER_DELETED",
        entity_type="User",
        entity_id=str(worker_uuid),
        module="manager",
        description=f"Manager soft-deleted {worker_role} {worker_name}.",
        ip_address=request.client.host if request.client else None,
        commit=False,
        required=True,
    )
    db.commit()
