from app.features.complaints.models import Ticket
from app.features.complaints.schemas import TicketResponse
from app.models.enums import Role, UserStatus


def _ward_manager_name(ticket: Ticket) -> str | None:
    if not ticket.zone:
        return None
    if ticket.zone.manager:
        return ticket.zone.manager.name
    # Legacy ward assignments keep the officer on users.zone_id rather than
    # zones.manager_id. Surface that assigned officer to the resident too.
    manager = next(
        (
            member
            for member in ticket.zone.members
            if member.role == Role.MUNICIPAL_OFFICER and member.status == UserStatus.ACTIVE
        ),
        None,
    )
    return manager.name if manager else None


def serialize_ticket(ticket: Ticket) -> TicketResponse:
    return TicketResponse(
        id=ticket.id,
        ref_code=ticket.ref_code,
        issue_type=ticket.issue_type.value,
        status=ticket.status.value,
        description=ticket.description,
        ward_code=ticket.zone.code if ticket.zone else None,
        ward_name=ticket.zone.name if ticket.zone else None,
        ward_sectors=ticket.zone.sectors if ticket.zone else None,
        ward_manager_name=_ward_manager_name(ticket),
        created_at=ticket.created_at,
    )
