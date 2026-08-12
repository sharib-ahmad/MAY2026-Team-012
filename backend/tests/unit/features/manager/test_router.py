from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.features.manager import router as manager_router
from app.features.manager.schemas import BulkPickupAssignment, TicketUpdate, WorkerUpdate
from app.models.enums import BulkRequestStatus, Role, TicketStatus, UserStatus


class FakeDatabase:
    """Small in-memory session double for manager command handlers."""

    def __init__(self, scalars=(), rowcount: int = 0):
        self._scalars = iter(scalars)
        self.rowcount = rowcount
        self.commits = 0
        self.added = []
        self.deleted = []

    def scalar(self, _statement):
        return next(self._scalars)

    def execute(self, _statement):
        return SimpleNamespace(rowcount=self.rowcount)

    def flush(self):
        """No-op flush for unit tests — real sessions flush to obtain IDs."""

    def commit(self):
        self.commits += 1

    def add_all(self, records):
        self.added.extend(records)

    def add(self, record):
        self.added.append(record)

    def delete(self, record):
        self.deleted.append(record)


@pytest.fixture
def manager():
    return SimpleNamespace(
        id=uuid4(),
        name="Morgan Manager",
        role=Role.MUNICIPAL_OFFICER,
        zone_id=uuid4(),
    )


def test_dashboard_delegates_to_dashboard_service(monkeypatch, manager) -> None:
    expected = {"stats": {"routes_today": 2}}
    db = FakeDatabase()
    monkeypatch.setattr(manager_router, "get_dashboard_data", lambda *_: expected)

    assert manager_router.get_manager_dashboard(manager, db) == expected


def test_mark_notifications_read_commits_and_returns_count(manager) -> None:
    db = FakeDatabase(rowcount=3)

    assert manager_router.mark_manager_notifications_read(manager, db) == {"marked_read": 3}
    assert db.commits == 1


def test_update_ticket_resolves_ticket_in_manager_ward(monkeypatch, manager) -> None:
    ticket = SimpleNamespace(
        id=uuid4(),
        zone_id=manager.zone_id,
        raised_by_id=uuid4(),
        ref_code="TK-0001",
        status=TicketStatus.OPEN,
        resolution_notes=None,
        resolved_at=None,
        resolved_by_id=None,
    )
    db = FakeDatabase([ticket])
    monkeypatch.setattr(manager_router, "get_managed_zone_ids", lambda *_: [manager.zone_id])

    result = manager_router.update_manager_ticket(
        str(ticket.id),
        TicketUpdate(status=TicketStatus.RESOLVED, resolution_notes="Cleared the blockage"),
        manager,
        db,
    )

    assert result == {"id": str(ticket.id), "status": "RESOLVED"}
    assert ticket.resolution_notes == "Cleared the blockage"
    assert ticket.resolved_by_id == manager.id
    assert db.added[0].user_id == ticket.raised_by_id
    assert "resolved" in db.added[0].body
    assert db.commits == 1


def test_update_ticket_requires_resolution_note(monkeypatch, manager) -> None:
    import warnings

    ticket = SimpleNamespace(id=uuid4(), zone_id=manager.zone_id)
    db = FakeDatabase([ticket])
    monkeypatch.setattr(manager_router, "get_managed_zone_ids", lambda *_: [manager.zone_id])

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        with pytest.raises(HTTPException, match="resolution note") as error:
            manager_router.update_manager_ticket(
                str(ticket.id), TicketUpdate(status=TicketStatus.RESOLVED), manager, db
            )

    assert error.value.status_code == 422


def test_assign_bulk_pickup_sets_assignment_and_notifies(monkeypatch, manager) -> None:
    request = SimpleNamespace(
        id=uuid4(),
        zone_id=manager.zone_id,
        requester_id=uuid4(),
        ref_code="BULK-12",
        assigned_collector_id=None,
        decided_by_id=None,
        decided_at=None,
        status=BulkRequestStatus.PENDING,
    )
    collector = SimpleNamespace(id=uuid4(), name="Casey Collector")
    db = FakeDatabase([request, collector])
    monkeypatch.setattr(manager_router, "get_managed_zone_ids", lambda *_: [manager.zone_id])

    result = manager_router.assign_bulk_pickup(
        str(request.id), BulkPickupAssignment(collector_id=str(collector.id)), manager, db
    )

    assert result == {
        "id": str(request.id),
        "status": "ASSIGNED",
        "collector_name": "Casey Collector",
    }
    assert request.assigned_collector_id == collector.id
    assert request.decided_by_id == manager.id
    assert request.status == BulkRequestStatus.ASSIGNED
    assert len(db.added) == 3  # 2 notifications + 1 audit log
    assert db.commits == 1


def test_manager_schemas_reject_invalid_identifiers_and_worker_status() -> None:
    with pytest.raises(ValidationError):
        BulkPickupAssignment(collector_id="not-a-uuid")
    with pytest.raises(ValidationError):
        WorkerUpdate(name="Casey", phone="123", status="PENDING")


def test_manager_cannot_mutate_recycler(monkeypatch, manager) -> None:
    recycler = SimpleNamespace(
        id=uuid4(),
        name="Reese Recycler",
        phone="111",
        status=UserStatus.ACTIVE,
        role=Role.RECYCLER,
        zone_id=manager.zone_id,
    )
    db = FakeDatabase([recycler])
    monkeypatch.setattr(manager_router, "get_managed_zone_ids", lambda *_: [manager.zone_id])

    with pytest.raises(HTTPException, match="Crew member not found") as error:
        manager_router.update_worker(
            recycler.id,
            WorkerUpdate(name="Reese", phone="111", status="ACTIVE"),
            SimpleNamespace(client=None),
            manager,
            db,
        )

    assert error.value.status_code == 404


def test_update_and_delete_worker_record_audit_events(monkeypatch, manager) -> None:
    worker = SimpleNamespace(
        id=uuid4(),
        name="Old Name",
        phone="111",
        status=UserStatus.ACTIVE,
        role=Role.COLLECTION_WORKER,
        zone_id=manager.zone_id,
        token_version=0,
    )
    # scalars: update_worker lookup, delete_worker lookup, delete_worker active-pickup check (None)
    db = FakeDatabase([worker, worker, None])
    audit_events = []
    monkeypatch.setattr(manager_router, "get_managed_zone_ids", lambda *_: [manager.zone_id])
    monkeypatch.setattr(
        manager_router, "create_audit_log", lambda *args, **kwargs: audit_events.append(kwargs)
    )

    result = manager_router.update_worker(
        str(worker.id),
        WorkerUpdate(name="  New Name  ", phone=" 222 ", status="INACTIVE"),
        SimpleNamespace(client=None),
        manager,
        db,
    )

    assert result == {
        "id": str(worker.id),
        "name": "New Name",
        "phone": "222",
        "status": "INACTIVE",
    }
    assert worker.status == UserStatus.DISABLED
    assert audit_events[0]["action"] == "CREW_MEMBER_UPDATED"

    deleted = manager_router.delete_worker(
        str(worker.id), SimpleNamespace(client=None), manager, db
    )

    assert deleted is None
    assert worker.deleted_at is not None
    assert worker.status == UserStatus.DISABLED
    assert db.deleted == []
    assert audit_events[1]["action"] == "CREW_MEMBER_DELETED"
