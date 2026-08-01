from types import SimpleNamespace
from uuid import uuid4

from app.features.complaints.service import serialize_ticket
from app.models.enums import Role, TicketStatus, TicketType, UserStatus


def test_serialize_ticket_uses_active_legacy_ward_manager() -> None:
    """Residents can see managers assigned through the legacy zone membership."""

    ticket = SimpleNamespace(
        id=uuid4(),
        ref_code="TK-1234",
        issue_type=TicketType.OVERFLOW,
        status=TicketStatus.OPEN,
        description="Bin has overflowed near the entrance.",
        resolution_notes=None,
        created_at="2026-08-01T10:00:00Z",
        zone=SimpleNamespace(
            code="W-04",
            name="Ward 4",
            sectors="A, B",
            manager=None,
            members=[
                SimpleNamespace(
                    name="Assigned Manager",
                    role=Role.MUNICIPAL_OFFICER,
                    status=UserStatus.ACTIVE,
                )
            ],
        ),
    )

    ticket_response = serialize_ticket(ticket)

    assert ticket_response.ward_manager_name == "Assigned Manager"
