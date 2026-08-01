import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.features.complaints.models import Ticket
from app.features.complaints.schemas import TicketCreate, TicketResponse, TicketsResponse
from app.features.complaints.service import serialize_ticket
from app.features.manager.service import notify_zone_managers
from app.features.notifications.models import Notification
from app.features.users.dependencies import require_resident
from app.features.users.models import User
from app.models.enums import TicketStatus, TicketType
from app.models.zone import Zone

router = APIRouter(tags=["Resident Complaints"])


@router.get("/tickets", response_model=TicketsResponse)
def list_tickets(
    current_user: User = Depends(require_resident), db: Session = Depends(get_db)
) -> TicketsResponse:
    tickets = (
        db.scalars(
            select(Ticket)
            .where(Ticket.raised_by_id == current_user.id)
            .options(joinedload(Ticket.zone).joinedload(Zone.manager))
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
    current_user: User = Depends(require_resident),
    db: Session = Depends(get_db),
) -> TicketResponse:
    if not current_user.zone_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Assign a ward before raising a complaint.",
        )
    ticket = Ticket(
        ref_code=f"TK-{uuid.uuid4().hex[:8].upper()}",
        raised_by_id=current_user.id,
        zone_id=current_user.zone_id,
        issue_type=TicketType(payload.issue_type),
        status=TicketStatus.OPEN,
        description=payload.description.strip(),
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
        .options(joinedload(Ticket.zone).joinedload(Zone.manager))
    )
    return serialize_ticket(ticket)
