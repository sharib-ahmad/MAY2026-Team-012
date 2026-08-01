from types import SimpleNamespace

from app.features.manager.service import _schedule_status, _ticket_severity
from app.models.enums import TicketType


def test_operational_ticket_types_are_high_priority() -> None:
    ticket = SimpleNamespace(issue_type=TicketType.MISSED_PICKUP)

    assert _ticket_severity(ticket) == "HIGH"


def test_other_ticket_types_are_medium_priority() -> None:
    ticket = SimpleNamespace(issue_type=TicketType.OTHER)

    assert _ticket_severity(ticket) == "MEDIUM"


def test_completed_schedule_returns_completed_status() -> None:
    schedule = SimpleNamespace(completed_at=None, total_stops=4, completed_stops=4)

    assert _schedule_status(schedule) == "COMPLETED"


def test_partially_completed_schedule_returns_in_progress_status() -> None:
    schedule = SimpleNamespace(completed_at=None, total_stops=4, completed_stops=2)

    assert _schedule_status(schedule) == "IN_PROGRESS"


def test_unstarted_schedule_returns_assigned_status() -> None:
    schedule = SimpleNamespace(completed_at=None, total_stops=4, completed_stops=0)

    assert _schedule_status(schedule) == "ASSIGNED"
