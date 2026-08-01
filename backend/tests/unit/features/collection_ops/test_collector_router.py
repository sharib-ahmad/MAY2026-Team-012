from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.features.collection_ops import router as collector_module
from app.features.collection_ops.schemas import DelayStopRequest, MixedWasteRequest
from app.models.enums import BulkRequestStatus, PickupStopStatus, WasteSeverity


class ScalarResult:
    def __init__(self, values):
        self.values = values

    def unique(self):
        return self

    def all(self):
        return self.values


class FakeDatabase:
    def __init__(self, scalars=(), scalar=None, rowcount=0):
        self.scalars_values = list(scalars)
        self.scalar_value = scalar
        self.rowcount = rowcount
        self.added = []
        self.commits = 0
        self.refreshed = []

    def scalars(self, _statement):
        return ScalarResult(self.scalars_values.pop(0))

    def scalar(self, _statement):
        return self.scalar_value

    def add(self, value):
        self.added.append(value)

    def commit(self):
        self.commits += 1

    def refresh(self, value):
        self.refreshed.append(value)

    def execute(self, _statement):
        return SimpleNamespace(rowcount=self.rowcount)


@pytest.fixture
def collector():
    return SimpleNamespace(id=uuid4(), name="Casey Collector", latitude=26.1, longitude=91.7)


@pytest.fixture
def assigned_pickup(collector):
    return SimpleNamespace(
        id=uuid4(),
        ref_code="BULK-001",
        requester_id=uuid4(),
        requester=SimpleNamespace(name="Riya Resident", latitude=26.2, longitude=91.8),
        zone_id=uuid4(),
        zone=SimpleNamespace(code="W-04", name="Ward Four"),
        category="DRY",
        estimated_weight=8,
        notes="12 Green Street",
        time_slot="09:00-11:00",
        status=BulkRequestStatus.ASSIGNED,
        collected_at=None,
        is_flagged=False,
        flag_severity=None,
        flag_note=None,
        assigned_collector_id=collector.id,
        requested_date=datetime(2026, 8, 1, tzinfo=UTC),
        created_at=datetime(2026, 7, 31, tzinfo=UTC),
    )


def test_collector_route_orders_active_pickups_before_completed(collector, assigned_pickup) -> None:
    completed = SimpleNamespace(
        **{
            **assigned_pickup.__dict__,
            "id": uuid4(),
            "ref_code": "BULK-002",
            "status": BulkRequestStatus.COLLECTED,
            "collected_at": datetime.now(UTC),
            "is_flagged": True,
        }
    )
    db = FakeDatabase(scalars=[[completed, assigned_pickup]])

    response = collector_module.get_collector_route(collector, db)

    assert response.pickup_count == 2
    assert response.completed_count == 1
    assert response.flagged_count == 1
    assert [pickup.ref_code for pickup in response.ordered_pickups] == ["BULK-001", "BULK-002"]
    assert response.ordered_pickups[0].pickup_order == 1
    assert response.ordered_pickups[1].pickup_order == 0


def test_resident_can_view_daily_pickup_schedule() -> None:
    resident = SimpleNamespace(id=uuid4())
    schedule = SimpleNamespace(
        id=uuid4(),
        schedule_date=datetime(2026, 8, 1, tzinfo=UTC),
        collector=SimpleNamespace(name="Casey Collector"),
        total_stops=3,
        completed_stops=1,
    )
    stop = SimpleNamespace(
        schedule=schedule,
        pickup_order=2,
        status=PickupStopStatus.PENDING,
    )

    response = collector_module.list_daily_pickup_schedules(
        resident, FakeDatabase(scalars=[[stop]])
    )

    assert response[0].schedule_id == schedule.id
    assert response[0].collector_name == "Casey Collector"
    assert response[0].completed_stops == 1


def test_collector_stop_serializes_route_stop() -> None:
    stop = SimpleNamespace(
        id=uuid4(),
        pickup=SimpleNamespace(
            ref_code="COL-BULK-001",
            status=BulkRequestStatus.ASSIGNED,
            category="DRY",
            estimated_weight=5,
            time_slot="09:00-11:00",
        ),
        pickup_order=1,
        status=PickupStopStatus.PENDING,
        resident=SimpleNamespace(name="Riya Resident"),
        schedule=SimpleNamespace(zone=SimpleNamespace(name="Ward Four")),
        notes="12 Green Street",
        latitude=26.2,
        longitude=91.8,
        completed_at=None,
    )

    response = collector_module._collector_stop(stop, is_flagged=True)

    assert response.ref_code == "COL-BULK-001"
    assert response.resident_name == "Riya Resident"
    assert response.is_flagged


@pytest.mark.parametrize(
    "lookup", [collector_module._owned_bulk_pickup, collector_module._owned_stop]
)
def test_collector_cannot_access_unassigned_pickup_or_stop(lookup, collector) -> None:
    with pytest.raises(HTTPException, match="Assigned pickup not found") as error:
        lookup(FakeDatabase(scalar=None), uuid4(), collector.id)

    assert error.value.status_code == 404


def test_complete_stop_records_collection_and_notifies(
    monkeypatch, collector, assigned_pickup
) -> None:
    db = FakeDatabase()
    monkeypatch.setattr(collector_module, "_owned_bulk_pickup", lambda *_: assigned_pickup)

    response = collector_module.complete_stop(assigned_pickup.id, collector, db)

    assert assigned_pickup.status == BulkRequestStatus.COLLECTED
    assert assigned_pickup.collected_at is not None
    assert response.status == "COLLECTED"
    assert db.added[0].title == "Pickup collected"
    assert db.commits == 1


def test_undo_complete_stop_restores_assigned_pickup(
    monkeypatch, collector, assigned_pickup
) -> None:
    assigned_pickup.status = BulkRequestStatus.COLLECTED
    assigned_pickup.collected_at = datetime.now(UTC)
    assigned_pickup.is_flagged = True
    assigned_pickup.flag_severity = WasteSeverity.HAZARDOUS
    assigned_pickup.flag_note = "Mixed waste"
    db = FakeDatabase()
    monkeypatch.setattr(collector_module, "_owned_bulk_pickup", lambda *_: assigned_pickup)

    response = collector_module.undo_complete_stop(assigned_pickup.id, collector, db)

    assert response.status == "ASSIGNED"
    assert assigned_pickup.collected_at is None
    assert not assigned_pickup.is_flagged
    assert assigned_pickup.flag_severity is None
    assert db.commits == 1


@pytest.mark.parametrize(
    ("status", "completed_at", "message"),
    [
        (BulkRequestStatus.ASSIGNED, None, "not completed"),
        (BulkRequestStatus.COLLECTED, datetime.now(UTC) - timedelta(minutes=2), "expired"),
    ],
)
def test_undo_complete_stop_rejects_invalid_requests(
    monkeypatch, collector, assigned_pickup, status, completed_at, message
) -> None:
    assigned_pickup.status = status
    assigned_pickup.collected_at = completed_at
    monkeypatch.setattr(collector_module, "_owned_bulk_pickup", lambda *_: assigned_pickup)

    with pytest.raises(HTTPException, match=message) as error:
        collector_module.undo_complete_stop(assigned_pickup.id, collector, FakeDatabase())

    assert error.value.status_code == 409


def test_collector_can_view_completed_pickups(collector, assigned_pickup) -> None:
    assigned_pickup.status = BulkRequestStatus.COLLECTED
    assigned_pickup.collected_at = datetime.now(UTC)

    response = collector_module.list_completed_collections(
        collector, FakeDatabase(scalars=[[assigned_pickup]])
    )

    assert len(response) == 1
    assert response[0].pickup_order == 1
    assert response[0].is_flagged is False


def test_notify_resident_of_delay_adds_notification(
    monkeypatch, collector, assigned_pickup
) -> None:
    db = FakeDatabase()
    monkeypatch.setattr(collector_module, "_owned_bulk_pickup", lambda *_: assigned_pickup)

    response = collector_module.notify_resident_of_delay(
        assigned_pickup.id,
        DelayStopRequest(reason="HEAVY_TRAFFIC", message="  Traffic is slow today.  "),
        collector,
        db,
    )

    assert response == {"message": "Resident notified."}
    assert db.added[0].body == "Traffic is slow today."
    assert db.commits == 1


def test_flag_mixed_waste_completes_pickup_and_alerts_manager(
    monkeypatch, collector, assigned_pickup
) -> None:
    db = FakeDatabase()
    manager_notifications = []
    monkeypatch.setattr(collector_module, "_owned_bulk_pickup", lambda *_: assigned_pickup)
    monkeypatch.setattr(
        collector_module,
        "notify_zone_managers",
        lambda *args: manager_notifications.append(args),
    )

    response = collector_module.flag_mixed_waste(
        assigned_pickup.id,
        MixedWasteRequest(
            severity="HAZARDOUS", description="  Glass mixed with recyclable paper.  "
        ),
        collector,
        db,
    )

    assert response == {"message": "Flag recorded for manager review."}
    assert assigned_pickup.status == BulkRequestStatus.COLLECTED
    assert assigned_pickup.is_flagged
    assert assigned_pickup.flag_note == "Glass mixed with recyclable paper."
    assert len(manager_notifications) == 1
    assert db.added[0].title == "Pickup completed with a waste-quality flag"


def test_mark_clean_and_notification_helpers(monkeypatch, collector) -> None:
    pickup = SimpleNamespace(
        is_contaminated=True,
        contamination_cleared_by_id=None,
        contamination_cleared_at=None,
    )
    stop = SimpleNamespace(pickup=pickup)
    db = FakeDatabase(rowcount=2)
    monkeypatch.setattr(collector_module, "_owned_stop", lambda *_: stop)
    monkeypatch.setattr(collector_module, "list_for_user", lambda *_: ["notice"])
    monkeypatch.setattr(
        collector_module,
        "mark_read",
        lambda *_: SimpleNamespace(model_dump=lambda: {"id": "notice", "is_read": True}),
    )

    assert collector_module.mark_stop_clean(uuid4(), collector, db) == {
        "message": "Pickup marked clean."
    }
    assert pickup.contamination_cleared_by_id == collector.id
    assert collector_module.list_collector_notifications(collector, db) == ["notice"]
    assert collector_module.mark_collector_notification_read(uuid4(), collector, db) == {
        "id": "notice",
        "is_read": True,
    }
    assert collector_module.mark_all_collector_notifications_read(collector, db) == {
        "marked_read": 2
    }


def test_mark_notification_read_rejects_unknown_notification(monkeypatch, collector) -> None:
    monkeypatch.setattr(collector_module, "mark_read", lambda *_: None)

    with pytest.raises(HTTPException, match="Notification not found") as error:
        collector_module.mark_collector_notification_read(uuid4(), collector, FakeDatabase())

    assert error.value.status_code == 404


def test_schedule_helpers_cover_completion_and_time_window() -> None:
    schedule = SimpleNamespace(id=uuid4(), completed_stops=0, completed_at=None)
    stops = [
        SimpleNamespace(status=PickupStopStatus.COLLECTED),
        SimpleNamespace(status=PickupStopStatus.COLLECTED),
    ]
    collector_module._refresh_schedule_completion(schedule, FakeDatabase(scalars=[stops]))

    assert schedule.completed_stops == 2
    assert schedule.completed_at is not None
    assert collector_module._is_within_undo_window(datetime.now(UTC))
    assert not collector_module._is_within_undo_window(None)
