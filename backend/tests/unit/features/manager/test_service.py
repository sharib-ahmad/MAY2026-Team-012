from types import SimpleNamespace
from uuid import uuid4

from app.features.manager.service import (
    _schedule_status,
    _ticket_severity,
    get_managed_zone_ids,
)
from app.models.enums import Role, TicketType


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


class FakeDatabase:
    def __init__(self, scalars=None, scalar=None):
        self.scalars_values = scalars or []
        self.scalar_value = scalar
        self.added = []
        self.committed = 0

    def scalars(self, statement):
        return FakeScalars(self.scalars_values)

    def scalar(self, statement):
        return self.scalar_value

    def add(self, obj):
        self.added.append(obj)

    def add_all(self, objs):
        self.added.extend(objs)

    def commit(self):
        self.committed += 1


class FakeScalars:
    def __init__(self, values):
        self.values = values

    def unique(self):
        return self

    def all(self):
        return self.values

    def where(self, _):
        return self


def test_get_managed_zone_ids():
    manager = SimpleNamespace(
        id=uuid4(),
        zone_id=uuid4(),
        role=Role.MUNICIPAL_OFFICER,
    )
    db = FakeDatabase(scalars=[manager.zone_id])

    zone_ids = get_managed_zone_ids(db, manager)

    assert len(zone_ids) == 1
    assert manager.zone_id in zone_ids
