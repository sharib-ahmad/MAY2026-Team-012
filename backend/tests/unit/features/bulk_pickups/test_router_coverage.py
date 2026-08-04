from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.features.bulk_pickups import router as bulk_pickup_router
from app.models.enums import BulkRequestStatus


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

    def commit(self):
        self.committed += 1


class FakeScalars:
    def __init__(self, values):
        self.values = values

    def unique(self):
        return self

    def all(self):
        return self.values

    def order_by(self, _):
        return self

    def where(self, _):
        return self


def test_list_pickups_empty():
    """Test listing pickups when user has no pickups"""
    user = SimpleNamespace(id=uuid4(), zone_id=uuid4())
    db = FakeDatabase(scalars=[])

    result = bulk_pickup_router.list_pickups(user, db)

    assert len(result.pickups) == 0
    assert result.total == 0


def test_list_pickups_with_pickups():
    """Test listing pickups when user has pickups"""
    user = SimpleNamespace(id=uuid4(), zone_id=uuid4())
    request = SimpleNamespace(
        id=uuid4(),
        ref_code="BPR-12345678",
        waste_category=SimpleNamespace(label="Dry Waste"),
        category="DRY",
        requested_date=datetime.now(UTC) + timedelta(days=2),
        estimated_weight=10,
        time_slot="Morning (8-11)",
        status=BulkRequestStatus.PENDING,
        created_at=datetime.now(UTC),
        notes=None,
        zone=None,
        assigned_collector=None,
        is_flagged=False,
        flag_severity=None,
        flag_note=None,
    )
    db = FakeDatabase(scalars=[request])

    result = bulk_pickup_router.list_pickups(user, db)

    assert len(result.pickups) == 1
    assert result.total == 1


def test_cancel_pickup_not_found():
    """Test canceling a pickup that doesn't exist"""
    user = SimpleNamespace(id=uuid4(), zone_id=uuid4())
    db = FakeDatabase(scalar=None)

    with pytest.raises(HTTPException, match="Pickup not found"):
        bulk_pickup_router.cancel_pickup(uuid4(), user, db)


def test_cancel_pickup_invalid_status():
    """Test canceling a pickup that can't be cancelled"""
    user = SimpleNamespace(id=uuid4(), zone_id=uuid4())
    request = SimpleNamespace(
        id=uuid4(),
        status=BulkRequestStatus.COLLECTED,
    )
    db = FakeDatabase(scalar=request)

    with pytest.raises(HTTPException, match="no longer be cancelled"):
        bulk_pickup_router.cancel_pickup(uuid4(), user, db)


def test_cancel_pickup_success():
    """Test successful pickup cancellation"""
    user = SimpleNamespace(id=uuid4(), zone_id=uuid4())
    request = SimpleNamespace(
        id=uuid4(),
        ref_code="BPR-12345678",
        status=BulkRequestStatus.PENDING,
        waste_category=None,
        category="DRY",
        requested_date=datetime.now(UTC),
        estimated_weight=10,
        time_slot="Morning (8-11)",
        notes=None,
        zone=None,
        assigned_collector=None,
        is_flagged=False,
        flag_severity=None,
        flag_note=None,
        created_at=datetime.now(UTC),
    )
    db = FakeDatabase(scalar=request)

    bulk_pickup_router.cancel_pickup(request.id, user, db)

    assert request.status == BulkRequestStatus.CANCELLED
    assert db.committed == 1


def test_pickup_tracking_not_found():
    """Test tracking a pickup that doesn't exist"""
    user = SimpleNamespace(id=uuid4(), zone_id=uuid4())
    db = FakeDatabase(scalar=None)

    with pytest.raises(HTTPException, match="Pickup not found"):
        bulk_pickup_router.pickup_tracking(uuid4(), user, db)
