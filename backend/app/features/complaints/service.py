from app.features.complaints.models import Ticket
from app.features.complaints.schemas import TicketResponse


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
        ward_manager_name=ticket.zone.manager.name if ticket.zone and ticket.zone.manager else None,
        created_at=ticket.created_at,
    )
