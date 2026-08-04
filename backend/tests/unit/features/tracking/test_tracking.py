from datetime import UTC, datetime
from types import SimpleNamespace

from app.features.collection_ops.service import track_bulk_pickup, track_ticket
from app.models.enums import BulkRequestStatus, TicketStatus, TicketType


def test_track_ticket_returns_progress_without_citizen_details() -> None:
    created_at = datetime(2026, 8, 1, 10, tzinfo=UTC)
    ticket = SimpleNamespace(
        ref_code="TK-ABCD1234",
        issue_type=TicketType.OVERFLOW,
        status=TicketStatus.RESOLVED,
        created_at=created_at,
        updated_at=created_at,
    )

    result = track_ticket(ticket)

    assert result.entity_type == "TICKET"
    assert result.status == "RESOLVED"
    assert [event.stage for event in result.timeline] == ["OPEN", "RESOLVED"]
    assert result.citizen_name is None


def test_track_bulk_pickup_returns_progress() -> None:
    created_at = datetime(2026, 8, 1, 10, tzinfo=UTC)
    pickup = SimpleNamespace(
        ref_code="BPR-ABCD1234",
        category="DRY",
        requested_date=created_at,
        status=BulkRequestStatus.ASSIGNED,
        created_at=created_at,
        updated_at=created_at,
    )

    result = track_bulk_pickup(pickup)

    assert result.entity_type == "PICKUP"
    assert result.status == "ASSIGNED"
    assert [event.stage for event in result.timeline] == ["PENDING", "SCHEDULED"]
