from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.features.materials.schemas import RejectBatchRequest
from app.features.materials.service import accept_batch, process_batch, reject_batch
from app.models.enums import BatchStatus, BulkRequestStatus, PickupStatus


class ScalarResult:
    def __init__(self, value):
        self.value = value

    def unique(self):
        return self

    def one_or_none(self):
        return self.value

    def all(self):
        return self.value


class FakeDatabase:
    def __init__(self, batch=None, credit_factor=None, existing_credit=None, bulk_request=None):
        self.batch = batch
        self.credit_factor = credit_factor
        self.existing_credit = existing_credit
        self.bulk_request = bulk_request
        self.added = []
        self.commits = 0
        self.refreshes = 0
        self.scalar_calls = 0

    def scalars(self, _statement):
        stmt_str = str(_statement)
        if "FROM batches" in stmt_str:
            return ScalarResult(self.batch)
        return ScalarResult([uuid4()])

    def scalar(self, _statement):
        self.scalar_calls += 1
        stmt_str = str(_statement)
        if "bulk_pickup_requests" in stmt_str:
            return self.bulk_request
        elif "credit_factors" in stmt_str:
            return self.credit_factor
        elif "credits" in stmt_str:
            return self.existing_credit
        return None

    def add(self, value):
        self.added.append(value)

    def add_all(self, values):
        self.added.extend(values)

    def commit(self):
        self.commits += 1

    def refresh(self, value):
        self.refreshes += 1


@pytest.fixture
def recycler():
    return SimpleNamespace(id=uuid4(), name="Demo Recycler")


@pytest.fixture
def batch(recycler):
    pickup = SimpleNamespace(
        id=uuid4(),
        ref_code="COL-BPR-1234",
        category="DRY",
        actual_weight=15.0,
        estimated_weight=10.0,
        status=PickupStatus.ASSIGNED,
        citizen_id=uuid4(),
        credits_earned=None,
        co2_saved=None,
        completed_at=None,
    )
    return SimpleNamespace(
        id=uuid4(),
        ref_code="BAT-00001",
        status=BatchStatus.ASSIGNED,
        destination_recycler_id=recycler.id,
        destination_recycler=recycler,
        pickups=[pickup],
        declared_weight=15.0,
        processed_quantity=None,
        processed_at=None,
        rejected_at=None,
        rejection_reason=None,
        zone_id=uuid4(),
        zone=SimpleNamespace(code="W-04", name="Ward Four"),
        waste_category="DRY",
        final_weight=None,
        quality_status=None,
        contamination_note=None,
        remarks=None,
        collected_at=datetime.now(UTC),
        assigned_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_accept_batch_success(recycler, batch):
    bulk_request = SimpleNamespace(ref_code="BPR-1234", status=BulkRequestStatus.ASSIGNED)
    db = FakeDatabase(batch=batch, bulk_request=bulk_request)
    accept_batch(db, recycler, batch.id)

    assert batch.status == BatchStatus.PROCESSING
    assert batch.pickups[0].status == PickupStatus.PROCESSING
    assert bulk_request.status == BulkRequestStatus.PROCESSING
    assert db.commits == 1
    assert len(db.added) == 1
    assert db.added[0].title == "Pickup processing started"


def test_accept_batch_unauthorized(recycler, batch):
    batch.destination_recycler_id = uuid4()
    db = FakeDatabase(batch=batch)

    with pytest.raises(HTTPException) as exc:
        accept_batch(db, recycler, batch.id)
    assert exc.value.status_code == 403
    assert "Batch not assigned to you" in exc.value.detail


def test_accept_batch_conflict(recycler, batch):
    batch.status = BatchStatus.PROCESSING
    db = FakeDatabase(batch=batch)

    with pytest.raises(HTTPException) as exc:
        accept_batch(db, recycler, batch.id)
    assert exc.value.status_code == 409
    assert "Only assigned batches can be accepted" in exc.value.detail


def test_reject_batch_success(recycler, batch):
    db = FakeDatabase(batch=batch)
    reject_batch(db, recycler, batch.id, "Quality issue")

    assert batch.status == BatchStatus.COLLECTED
    assert batch.rejection_reason == "Quality issue"
    assert db.commits == 1


def test_reject_batch_request_whitespace_only():
    with pytest.raises(ValidationError):
        RejectBatchRequest(note="   ")


def test_process_batch_success(recycler, batch):
    batch.status = BatchStatus.PROCESSING
    credit_factor = SimpleNamespace(
        credit_rate=2.5,
        co2_factor=1.8,
    )
    bulk_request = SimpleNamespace(ref_code="BPR-1234", status=BulkRequestStatus.PROCESSING)
    db = FakeDatabase(batch=batch, credit_factor=credit_factor, bulk_request=bulk_request)

    process_batch(db, recycler, batch.id)

    assert batch.status == BatchStatus.PROCESSED
    assert batch.processed_quantity == 15.0
    assert batch.pickups[0].status == PickupStatus.PROCESSED
    assert batch.pickups[0].credits_earned == 37.5
    assert batch.pickups[0].co2_saved == 27.0
    assert bulk_request.status == BulkRequestStatus.PROCESSED
    assert db.commits == 1
