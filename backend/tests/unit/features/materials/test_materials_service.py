from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.features.materials.service import (
    _build_batch_groups,
    _next_batch_ref,
    _pickup_weight,
    _resolve_collector_id,
    _sync_bulk_pickup_status,
    assign_batch,
)
from app.models.enums import BulkRequestStatus


class FakeDatabase:
    def __init__(self, scalars=None, scalar=None):
        self.scalars_values = scalars or []
        self.scalar_value = scalar
        self.committed = 0

    def scalars(self, statement):
        return FakeScalars(self.scalars_values)

    def scalar(self, statement):
        return self.scalar_value

    def commit(self):
        self.committed += 1


class FakeScalars:
    def __init__(self, values):
        self.values = values

    def unique(self):
        return self

    def all(self):
        return self.values


def test_sync_bulk_pickup_status_with_valid_ref():
    pickup = SimpleNamespace(
        ref_code="COL-BULK-001",
        actual_weight=10.0,
        estimated_weight=10.0,
    )
    request = SimpleNamespace(
        id=uuid4(),
        status=BulkRequestStatus.ASSIGNED,
    )
    db = FakeDatabase(scalar=request)

    _sync_bulk_pickup_status(db, pickup, BulkRequestStatus.COLLECTED)

    assert request.status == BulkRequestStatus.COLLECTED


def test_sync_bulk_pickup_status_with_invalid_ref():
    pickup = SimpleNamespace(
        ref_code="INVALID-001",
        actual_weight=10.0,
        estimated_weight=10.0,
    )
    db = FakeDatabase(scalar=None)

    _sync_bulk_pickup_status(db, pickup, BulkRequestStatus.COLLECTED)

    # Should not raise exception


def test_next_batch_ref():
    db = FakeDatabase(scalar=5)

    ref = _next_batch_ref(db)

    assert ref == "BAT-00006"


def test_pickup_weight_with_actual_weight():
    pickup = SimpleNamespace(
        actual_weight=15.0,
        estimated_weight=10.0,
    )

    weight = _pickup_weight(pickup)

    assert weight == 15.0


def test_pickup_weight_without_actual_weight():
    pickup = SimpleNamespace(
        actual_weight=None,
        estimated_weight=10.0,
    )

    weight = _pickup_weight(pickup)

    assert weight == 10.0


def test_build_batch_groups_with_enough_weight(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "BATCH_THRESHOLD_KG", 30.0)
    pickup1 = SimpleNamespace(estimated_weight=15.0, actual_weight=None)
    pickup2 = SimpleNamespace(estimated_weight=20.0, actual_weight=None)
    pickup3 = SimpleNamespace(estimated_weight=10.0, actual_weight=None)

    groups = _build_batch_groups([pickup1, pickup2, pickup3])

    assert len(groups) == 1
    assert len(groups[0]) == 2


def test_build_batch_groups_without_enough_weight(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setattr(get_settings(), "BATCH_THRESHOLD_KG", 30.0)
    pickup1 = SimpleNamespace(estimated_weight=10.0, actual_weight=None)
    pickup2 = SimpleNamespace(estimated_weight=5.0, actual_weight=None)

    groups = _build_batch_groups([pickup1, pickup2])

    assert len(groups) == 0


def test_resolve_collector_id_from_pickup():
    pickup = SimpleNamespace(collector_id=uuid4())
    zone_id = uuid4()
    db = FakeDatabase()

    collector_id = _resolve_collector_id(db, zone_id, [pickup])

    assert collector_id == pickup.collector_id


def test_resolve_collector_id_from_db():
    pickup = SimpleNamespace(collector_id=None)
    zone_id = uuid4()
    collector_id = uuid4()
    db = FakeDatabase(scalar=collector_id)

    result = _resolve_collector_id(db, zone_id, [pickup])

    assert result == collector_id


def test_resolve_collector_id_not_found():
    pickup = SimpleNamespace(collector_id=None)
    zone_id = uuid4()
    db = FakeDatabase(scalar=None)

    with pytest.raises(HTTPException):  # Should raise when no collector found
        _resolve_collector_id(db, zone_id, [pickup])


def test_build_batch_groups_with_multiple_small_pickups():
    pickup1 = SimpleNamespace(estimated_weight=10.0, actual_weight=None)
    pickup2 = SimpleNamespace(estimated_weight=10.0, actual_weight=None)
    pickup3 = SimpleNamespace(estimated_weight=10.0, actual_weight=None)

    groups = _build_batch_groups([pickup1, pickup2, pickup3])

    assert len(groups) == 1
    assert len(groups[0]) == 3


def test_manager_without_managed_ward_cannot_assign_batch(monkeypatch):
    batch_id = uuid4()
    recycler_id = uuid4()
    batch_zone_id = uuid4()
    manager = SimpleNamespace(id=uuid4(), zone_id=None)
    batch = SimpleNamespace(id=batch_id, zone_id=batch_zone_id)

    db = FakeDatabase()

    monkeypatch.setattr("app.features.materials.service._load_batch", lambda _db, b_id: batch)
    monkeypatch.setattr("app.features.materials.service.get_managed_zone_ids", lambda _db, mgr: [])

    with pytest.raises(HTTPException) as exc_info:
        assign_batch(db, manager, batch_id, recycler_id)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Batch is outside your wards."
