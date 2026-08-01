from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.features.collection_ops import router as collector_module
from app.features.collection_ops.schemas import DelayStopRequest, MixedWasteRequest
from app.models.enums import BulkRequestStatus, PickupStatus, PickupStopStatus


class ScalarResult:
    def __init__(self, values):
        self.values = values

    def unique(self):
        return self

    def all(self):
        return self.values


class FakeDatabase:
    def __init__(self, scalars=(), scalar=None):
        self.scalars_values, self.scalar_value, self.added, self.commits = (
            list(scalars),
            scalar,
            [],
            0,
        )

    def scalars(self, _statement):
        return ScalarResult(self.scalars_values.pop(0))

    def scalar(self, _statement):
        return self.scalar_value

    def add(self, value):
        self.added.append(value)

    def flush(self):
        pass

    def commit(self):
        self.commits += 1

    def refresh(self, _value):
        pass


@pytest.fixture
def collector():
    return SimpleNamespace(id=uuid4(), name="Casey Collector", latitude=26.1, longitude=91.7)


@pytest.fixture
def stop():
    pickup = SimpleNamespace(
        ref_code="COL-BULK-001",
        category="DRY",
        estimated_weight=8,
        time_slot="09:00-11:00",
        status=PickupStatus.ASSIGNED,
        completed_at=None,
    )
    schedule = SimpleNamespace(
        id=uuid4(),
        zone_id=uuid4(),
        zone=SimpleNamespace(code="W-04", name="Ward Four"),
        completed_stops=0,
        completed_at=None,
    )
    return SimpleNamespace(
        id=uuid4(),
        pickup=pickup,
        resident_id=uuid4(),
        resident=SimpleNamespace(name="Riya Resident"),
        schedule=schedule,
        schedule_id=schedule.id,
        pickup_order=1,
        status=PickupStopStatus.PENDING,
        latitude=26.2,
        longitude=91.8,
        notes="12 Green Street",
        completed_at=None,
        mixed_waste_tags=[],
    )


def test_route_uses_persisted_daily_stops(monkeypatch, collector, stop):
    completed = SimpleNamespace(
        **{
            **stop.__dict__,
            "id": uuid4(),
            "status": PickupStopStatus.COLLECTED,
            "completed_at": datetime.now(UTC),
            "mixed_waste_tags": [object()],
        }
    )
    monkeypatch.setattr(collector_module, "_materialize_assigned_bulk_stops", lambda *_: False)
    response = collector_module.get_collector_route(
        collector, FakeDatabase(scalars=[[stop, completed]])
    )
    assert response.pickup_count == 2
    assert response.completed_count == 1
    assert response.flagged_count == 1
    assert response.ordered_pickups[0].id == stop.id
    assert [pickup.pickup_order for pickup in response.ordered_pickups] == [1, 2]


def test_route_commits_newly_materialized_stops(monkeypatch, collector, stop):
    db = FakeDatabase(scalars=[[stop]])
    monkeypatch.setattr(collector_module, "_materialize_assigned_bulk_stops", lambda *_: True)

    collector_module.get_collector_route(collector, db)

    assert db.commits == 1


def test_complete_updates_stop_and_schedule(monkeypatch, collector, stop):
    db = FakeDatabase(scalars=[[stop]])
    monkeypatch.setattr(collector_module, "_owned_stop", lambda *_: stop)
    response = collector_module.complete_stop(stop.id, collector, db)
    assert response.status == "COLLECTED"
    assert stop.pickup.status == PickupStatus.COLLECTED
    assert stop.schedule.completed_stops == 1
    assert db.added[0].title == "Pickup collected"


def test_complete_rejects_repeat(monkeypatch, collector, stop):
    stop.status = PickupStopStatus.COLLECTED
    monkeypatch.setattr(collector_module, "_owned_stop", lambda *_: stop)
    with pytest.raises(HTTPException, match="already collected") as error:
        collector_module.complete_stop(stop.id, collector, FakeDatabase())
    assert error.value.status_code == 409


def test_route_stop_completion_syncs_the_source_bulk_request(stop):
    bulk_request = SimpleNamespace(
        status=BulkRequestStatus.ASSIGNED,
        collected_at=None,
        is_flagged=False,
        flag_severity=None,
        flag_note=None,
    )
    db = FakeDatabase(scalar=bulk_request)
    collected_at = datetime.now(UTC)

    collector_module._sync_source_bulk_pickup(db, stop, BulkRequestStatus.COLLECTED, collected_at)

    assert bulk_request.status == BulkRequestStatus.COLLECTED
    assert bulk_request.collected_at == collected_at


def test_route_stop_flag_syncs_flag_details_to_the_source_bulk_request(stop):
    bulk_request = SimpleNamespace(
        status=BulkRequestStatus.ASSIGNED,
        collected_at=None,
        is_flagged=False,
        flag_severity=None,
        flag_note=None,
    )
    db = FakeDatabase(scalar=bulk_request)

    collector_module._sync_source_bulk_pickup(
        db,
        stop,
        BulkRequestStatus.COLLECTED,
        datetime.now(UTC),
        is_flagged=True,
        flag_severity="HAZARDOUS",
        flag_note="Sharp glass mixed with dry waste.",
    )

    assert bulk_request.is_flagged is True
    assert bulk_request.flag_severity == "HAZARDOUS"
    assert bulk_request.flag_note == "Sharp glass mixed with dry waste."


def test_undo_restores_pending_stop(monkeypatch, collector, stop):
    stop.status, stop.completed_at = PickupStopStatus.COLLECTED, datetime.now(UTC)
    stop.pickup.status = PickupStatus.COLLECTED
    db = FakeDatabase(scalars=[[stop]])
    monkeypatch.setattr(collector_module, "_owned_stop", lambda *_: stop)
    response = collector_module.undo_complete_stop(stop.id, collector, db)
    assert response.status == "PENDING"
    assert stop.pickup.status == PickupStatus.ASSIGNED


def test_delay_creates_log_and_notification(monkeypatch, collector, stop):
    db = FakeDatabase()
    monkeypatch.setattr(collector_module, "_owned_stop", lambda *_: stop)
    collector_module.notify_resident_of_delay(
        stop.id,
        DelayStopRequest(reason="HEAVY_TRAFFIC", message=" Traffic is slow. "),
        collector,
        db,
    )
    assert stop.status == PickupStopStatus.DELAYED
    assert db.added[0].note == "Traffic is slow."
    assert db.added[1].body == "Traffic is slow."


def test_flag_creates_manager_review_record(monkeypatch, collector, stop):
    db, notices = FakeDatabase(scalars=[[stop]]), []
    monkeypatch.setattr(collector_module, "_owned_stop", lambda *_: stop)
    monkeypatch.setattr(
        collector_module, "notify_zone_managers", lambda *args: notices.append(args)
    )
    collector_module.flag_mixed_waste(
        stop.id,
        MixedWasteRequest(severity="HAZARDOUS", description=" Glass mixed with paper. "),
        collector,
        db,
    )
    assert stop.status == PickupStopStatus.COLLECTED
    assert db.added[0].note == "Glass mixed with paper."
    assert len(notices) == 1


def test_undo_window():
    assert collector_module._is_within_undo_window(datetime.now(UTC))
    assert not collector_module._is_within_undo_window(datetime.now(UTC) - timedelta(minutes=2))
