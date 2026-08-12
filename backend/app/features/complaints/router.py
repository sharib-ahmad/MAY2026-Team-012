import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.features.complaints.models import Ticket
from app.features.complaints.schemas import (
    TicketCreate,
    TicketReopenRequest,
    TicketResponse,
    TicketsResponse,
)
from app.features.complaints.service import serialize_ticket
from app.features.manager.service import notify_zone_managers
from app.features.notifications.models import Notification
from app.features.users.dependencies import require_citizen
from app.features.users.models import User
from app.models.enums import TicketStatus, TicketType
from app.models.zone import Zone

router = APIRouter(tags=["Citizen Complaints"])

# Handle Starlette version differences for HTTP status codes
try:
    HTTP_422 = status.HTTP_422_UNPROCESSABLE_CONTENT
except AttributeError:
    HTTP_422 = status.HTTP_422_UNPROCESSABLE_ENTITY


@router.get("/tickets", response_model=TicketsResponse)
def list_tickets(
    current_user: User = Depends(require_citizen), db: Session = Depends(get_db)
) -> TicketsResponse:
    tickets = (
        db.scalars(
            select(Ticket)
            .where(Ticket.raised_by_id == current_user.id)
            .options(
                joinedload(Ticket.zone).joinedload(Zone.manager),
                joinedload(Ticket.zone).joinedload(Zone.members),
            )
            .order_by(Ticket.created_at.desc())
        )
        .unique()
        .all()
    )
    return TicketsResponse(
        tickets=[serialize_ticket(ticket) for ticket in tickets], total=len(tickets)
    )


@router.post("/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
) -> TicketResponse:
    if not current_user.zone_id:
        raise HTTPException(
            status_code=HTTP_422,
            detail="Assign a ward before raising a complaint.",
        )
    ticket = Ticket(
        ref_code=f"TK-{uuid.uuid4().hex[:8].upper()}",
        raised_by_id=current_user.id,
        zone_id=current_user.zone_id,
        issue_type=TicketType(payload.issue_type),
        status=TicketStatus.OPEN,
        description=payload.description,
    )
    db.add(ticket)
    db.add(
        Notification(
            user_id=current_user.id,
            title="Complaint submitted",
            body=f"Your complaint {ticket.ref_code} has been submitted.",
        )
    )
    notify_zone_managers(
        db,
        ticket.zone_id,
        "New citizen complaint",
        f"{ticket.ref_code} was raised in your ward: {ticket.description[:120]}",
    )
    db.commit()
    ticket = db.scalar(
        select(Ticket)
        .where(Ticket.id == ticket.id)
        .options(
            joinedload(Ticket.zone).joinedload(Zone.manager),
            joinedload(Ticket.zone).joinedload(Zone.members),
        )
    )
    return serialize_ticket(ticket)


@router.post("/tickets/{ticket_id}/reopen", response_model=TicketResponse)
@router.post("/{ticket_id}/reopen", response_model=TicketResponse)
def reopen_ticket(
    ticket_id: uuid.UUID,
    payload: TicketReopenRequest,
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
) -> TicketResponse:
    """Reopen a resolved complaint within 24 hours with a citizen note."""
    ticket = db.scalar(
        select(Ticket)
        .where(
            Ticket.id == ticket_id,
            Ticket.raised_by_id == current_user.id,
        )
        .options(
            joinedload(Ticket.zone).joinedload(Zone.manager),
            joinedload(Ticket.zone).joinedload(Zone.members),
        )
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    now = datetime.now(UTC)
    # Check if ticket was resolved over 24 hours ago
    if (
        ticket.status == TicketStatus.RESOLVED
        and ticket.resolved_at
        and (now - ticket.resolved_at) > timedelta(hours=24)
    ):
        ticket.status = TicketStatus.CLOSED
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Complaint was resolved over 24 hours ago and is now closed.",
        )

    if ticket.status != TicketStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only recently resolved complaints can be reopened.",
        )

    ticket.status = TicketStatus.OPEN
    ticket.description = f"{ticket.description}\n[Reopened Note]: {payload.note}"
    ticket.resolved_at = None
    ticket.resolved_by_id = None
    db.commit()
    db.refresh(ticket)
    return serialize_ticket(ticket)
