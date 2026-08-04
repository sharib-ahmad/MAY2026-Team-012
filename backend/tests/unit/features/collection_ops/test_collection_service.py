from datetime import UTC, datetime
from types import SimpleNamespace

from app.features.collection_ops.service import (
    _event,
    _resolve_manager_name,
    track_bulk_pickup,
    track_pickup,
    track_ticket,
)
from app.models.enums import BatchStatus, PickupStatus


def test_event_creation():
    event = _event("PENDING", "Test event", datetime.now(UTC))

    assert event.stage == "PENDING"
    assert event.label == "Test event"
    assert event.at is not None


def test_resolve_manager_name_from_default():
    manager = SimpleNamespace(name="John Manager")

    result = _resolve_manager_name(None, manager)

    assert result == "John Manager"


def test_resolve_manager_name_from_string():
    result = _resolve_manager_name(None, "Jane Manager")

    assert result == "Jane Manager"


def test_resolve_manager_name_from_zone_manager():
    manager = SimpleNamespace(name="Zone Manager")
    zone = SimpleNamespace(manager=manager)

    result = _resolve_manager_name(zone, None)

    assert result == "Zone Manager"


def test_resolve_manager_name_from_zone_members():
    member = SimpleNamespace(
        name="Member Manager",
        role=SimpleNamespace(value="MUNICIPAL_OFFICER"),
    )
    zone = SimpleNamespace(manager=None, members=[member])

    result = _resolve_manager_name(zone, None)

    assert result == "Member Manager"


def test_resolve_manager_name_none():
    result = _resolve_manager_name(None, None)

    assert result is None


def test_track_ticket_open():
    ticket = SimpleNamespace(
        ref_code="TCK-001",
        status=SimpleNamespace(value="OPEN"),
        issue_type=SimpleNamespace(value="MISSED_COLLECTION"),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        raised_by=SimpleNamespace(name="Citizen"),
        zone=SimpleNamespace(name="Ward 1"),
        resolved_by=None,
    )

    result = track_ticket(ticket)

    assert result.ref_code == "TCK-001"
    assert result.status == "OPEN"
    assert len(result.timeline) == 1
    assert result.citizen_name == "Citizen"
    assert result.zone_name == "Ward 1"


def test_track_ticket_resolved():
    ticket = SimpleNamespace(
        ref_code="TCK-001",
        status=SimpleNamespace(value="RESOLVED"),
        issue_type=SimpleNamespace(value="MISSED_COLLECTION"),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        raised_by=SimpleNamespace(name="Citizen"),
        zone=SimpleNamespace(name="Ward 1"),
        resolved_by=SimpleNamespace(name="Manager"),
    )

    result = track_ticket(ticket)

    assert result.status == "RESOLVED"
    assert len(result.timeline) == 2
    assert result.manager_name == "Manager"


def test_track_bulk_pickup_pending():
    request = SimpleNamespace(
        ref_code="BPR-001",
        status=SimpleNamespace(value="PENDING"),
        category="DRY",
        requested_date=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        requester=SimpleNamespace(name="Citizen"),
        zone=SimpleNamespace(name="Ward 1"),
        decided_by=None,
        assigned_collector=None,
    )

    result = track_bulk_pickup(request, pickup=None)

    assert result.ref_code == "BPR-001"
    assert result.status == "PENDING"
    assert len(result.timeline) == 1
    assert result.citizen_name == "Citizen"


def test_track_bulk_pickup_assigned():
    request = SimpleNamespace(
        ref_code="BPR-001",
        status=SimpleNamespace(value="ASSIGNED"),
        category="DRY",
        requested_date=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        requester=SimpleNamespace(name="Citizen"),
        zone=SimpleNamespace(name="Ward 1"),
        decided_by=SimpleNamespace(name="Manager"),
        assigned_collector=SimpleNamespace(name="Collector"),
    )

    result = track_bulk_pickup(request, pickup=None)

    assert result.status == "ASSIGNED"
    assert len(result.timeline) == 2
    assert result.manager_name == "Manager"
    assert result.collector_name == "Collector"


def test_track_pickup_pending():
    pickup = SimpleNamespace(
        ref_code="COL-001",
        status=PickupStatus.PENDING,
        category="DRY",
        scheduled_date=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        completed_at=None,
        batch=None,
        credits_earned=None,
        citizen=SimpleNamespace(name="Citizen"),
        zone=SimpleNamespace(name="Ward 1"),
        collector=SimpleNamespace(name="Collector"),
    )

    result = track_pickup(pickup)

    assert result.ref_code == "COL-001"
    assert result.status == "PENDING"
    assert len(result.timeline) == 1


def test_track_pickup_scheduled():
    pickup = SimpleNamespace(
        ref_code="COL-001",
        status=PickupStatus.SCHEDULED,
        category="DRY",
        scheduled_date=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        completed_at=None,
        batch=None,
        credits_earned=None,
        citizen=SimpleNamespace(name="Citizen"),
        zone=SimpleNamespace(name="Ward 1"),
        collector=SimpleNamespace(name="Collector"),
    )

    result = track_pickup(pickup)

    assert result.status == "SCHEDULED"
    assert len(result.timeline) == 2


def test_track_pickup_collected():
    pickup = SimpleNamespace(
        ref_code="COL-001",
        status=PickupStatus.COLLECTED,
        category="DRY",
        scheduled_date=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        batch=None,
        credits_earned=None,
        citizen=SimpleNamespace(name="Citizen"),
        zone=SimpleNamespace(name="Ward 1"),
        collector=SimpleNamespace(name="Collector"),
    )

    result = track_pickup(pickup)

    assert result.status == "COLLECTED"
    assert len(result.timeline) == 3


def test_track_pickup_with_batch():
    batch = SimpleNamespace(
        ref_code="BAT-001",
        status=BatchStatus.ASSIGNED,
        collected_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        assigned_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        processed_at=None,
        assigned_by=SimpleNamespace(name="Manager"),
        destination_recycler=SimpleNamespace(name="Recycler"),
    )
    pickup = SimpleNamespace(
        ref_code="COL-001",
        status=PickupStatus.COLLECTED,
        category="DRY",
        scheduled_date=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        batch=batch,
        credits_earned=None,
        citizen=SimpleNamespace(name="Citizen"),
        zone=SimpleNamespace(name="Ward 1"),
        collector=SimpleNamespace(name="Collector"),
    )

    result = track_pickup(pickup)

    assert len(result.timeline) == 5
    assert result.manager_name == "Manager"
    assert result.recycler_name == "Recycler"
