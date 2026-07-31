from datetime import UTC, datetime, timedelta

import pytest

from app.features.collection_ops.models import (
    DailyPickupSchedule,
    DailyPickupStop,
    DelayLog,
    MixedWasteTag,
    Pickup,
    RouteHistory,
)
from app.features.complaints.models import Ticket
from app.features.manager.schemas import ComplaintUpdate
from app.features.manager.service import (
    get_overview,
    get_route_detail,
    list_complaints,
    list_routes,
    list_workers,
    reassign_worker,
    update_complaint,
)
from app.features.sorting_guide.models import WasteCategory
from app.features.users.models import User
from app.models.enums import (
    Availability,
    DelayReason,
    PickupStatus,
    PickupStopStatus,
    Role,
    TicketStatus,
    TicketType,
    UserStatus,
    WasteSeverity,
)
from app.models.zone import Zone


@pytest.fixture
def manager_session(db):
    yield db


@pytest.mark.unit
def test_get_overview_builds_dashboard_summary(manager_session):
    now = datetime.now(UTC)
    zone = Zone(name="Ward A", code="W-10")
    manager_session.add(zone)
    manager_session.flush()

    resident = User(
        name="Resident One",
        email="resident@example.com",
        password_hash="hash",
        phone="+910000000001",
        role=Role.CITIZEN,
        status=UserStatus.ACTIVE,
        zone_id=zone.id,
    )
    worker = User(
        name="Collector One",
        email="collector@example.com",
        password_hash="hash",
        phone="+910000000002",
        role=Role.COLLECTION_WORKER,
        status=UserStatus.ACTIVE,
        zone_id=zone.id,
        availability=Availability.AVAILABLE,
    )
    manager_session.add_all([resident, worker])
    manager_session.flush()

    category = WasteCategory(code="WET", label="Wet Waste", sort_order=1, is_active=True)
    manager_session.add(category)
    manager_session.flush()

    pickup = Pickup(
        ref_code="PK-001",
        resident_id=resident.id,
        zone_id=zone.id,
        category=category.code,
        estimated_weight=3.5,
        status=PickupStatus.COMPLETED,
    )
    manager_session.add(pickup)
    manager_session.flush()

    schedule = DailyPickupSchedule(
        collector_id=worker.id,
        zone_id=zone.id,
        schedule_date=now,
        total_stops=3,
        completed_stops=2,
        is_active=True,
    )
    manager_session.add(schedule)
    manager_session.flush()

    stop = DailyPickupStop(
        pickup_id=pickup.id,
        schedule_id=schedule.id,
        resident_id=resident.id,
        pickup_order=1,
        status=PickupStopStatus.COLLECTED,
    )
    manager_session.add(stop)
    manager_session.flush()

    manager_session.add(
        RouteHistory(
            schedule_id=schedule.id, started_at=now - timedelta(minutes=10), completed_at=now
        )
    )
    manager_session.add(
        DelayLog(
            stop_id=stop.id,
            worker_id=worker.id,
            reason=DelayReason.OTHER,
            note="Traffic jam",
        )
    )
    manager_session.add(
        MixedWasteTag(
            stop_id=stop.id,
            worker_id=worker.id,
            severity=WasteSeverity.HAZARDOUS,
            note="Mixed waste",
        )
    )
    manager_session.add(
        Ticket(
            ref_code="CMP-001",
            raised_by_id=resident.id,
            zone_id=zone.id,
            issue_type=TicketType.OTHER,
            status=TicketStatus.OPEN,
            description="The bin is overflowing and needs attention",
            created_at=now - timedelta(days=4),
        )
    )
    manager_session.commit()

    overview = get_overview(manager_session, None)

    assert overview.stats.routes_today == 1
    assert overview.stats.open_complaints == 1
    assert overview.wards[0].coverage_pct == 67
    assert overview.needs_attention[0].ref_code == "CMP-001"
    assert overview.mixed_waste_flags[0].note == "Mixed waste"


@pytest.mark.unit
def test_complaint_listing_update_and_error_paths(manager_session):
    now = datetime.now(UTC)
    zone = Zone(name="Ward B", code="W-11")
    manager_session.add(zone)
    manager_session.flush()

    resident = User(
        name="Resident Two",
        email="resident2@example.com",
        password_hash="hash",
        phone="+910000000003",
        role=Role.CITIZEN,
        status=UserStatus.ACTIVE,
        zone_id=zone.id,
    )
    manager = User(
        name="Manager Two",
        email="manager2@example.com",
        password_hash="hash",
        phone="+910000000004",
        role=Role.MUNICIPAL_OFFICER,
        status=UserStatus.ACTIVE,
        zone_id=zone.id,
    )
    manager_session.add_all([resident, manager])
    manager_session.flush()

    ticket = Ticket(
        ref_code="CMP-002",
        raised_by_id=resident.id,
        zone_id=zone.id,
        issue_type=TicketType.DELAY,
        status=TicketStatus.OPEN,
        description="Leak in the waste chute",
        created_at=now - timedelta(days=1),
    )
    manager_session.add(ticket)
    manager_session.commit()

    complaints = list_complaints(
        manager_session, None, zone_code=zone.code, status="OPEN", search="chute"
    )
    assert complaints.total == 1
    assert complaints.complaints[0].ref_code == "CMP-002"

    updated = update_complaint(
        manager_session,
        str(ticket.id),
        ComplaintUpdate(status="RESOLVED", resolution_notes="Fixed"),
        manager,
        [zone.id],
    )
    assert updated.status == "RESOLVED"

    with pytest.raises(ValueError, match="Invalid complaint ID format"):
        update_complaint(
            manager_session, "bad-id", ComplaintUpdate(status="RESOLVED"), manager, [zone.id]
        )

    with pytest.raises(ValueError, match="A resolution note is required"):
        update_complaint(
            manager_session,
            str(ticket.id),
            ComplaintUpdate(status="RESOLVED", resolution_notes="   "),
            manager,
            [zone.id],
        )


@pytest.mark.unit
def test_routes_workers_and_reassignment_flow(manager_session):
    now = datetime.now(UTC)
    zone = Zone(name="Ward C", code="W-12")
    manager_session.add(zone)
    manager_session.flush()

    worker = User(
        name="Collector Three",
        email="collector3@example.com",
        password_hash="hash",
        phone="+910000000005",
        role=Role.COLLECTION_WORKER,
        status=UserStatus.ACTIVE,
        zone_id=zone.id,
        availability=Availability.ON_ROUTE,
    )
    resident = User(
        name="Resident Three",
        email="resident3@example.com",
        password_hash="hash",
        phone="+910000000006",
        role=Role.CITIZEN,
        status=UserStatus.ACTIVE,
        zone_id=zone.id,
    )
    manager_session.add_all([worker, resident])
    manager_session.flush()

    category = WasteCategory(code="DRY", label="Dry Waste", sort_order=2, is_active=True)
    manager_session.add(category)
    manager_session.flush()

    pickup = Pickup(
        ref_code="PK-002",
        resident_id=resident.id,
        zone_id=zone.id,
        category=category.code,
        estimated_weight=2.0,
        status=PickupStatus.SCHEDULED,
    )
    manager_session.add(pickup)
    manager_session.flush()

    schedule = DailyPickupSchedule(
        collector_id=worker.id,
        zone_id=zone.id,
        schedule_date=now,
        total_stops=1,
        completed_stops=0,
        is_active=True,
    )
    manager_session.add(schedule)
    manager_session.flush()

    stop = DailyPickupStop(
        pickup_id=pickup.id,
        schedule_id=schedule.id,
        resident_id=resident.id,
        pickup_order=1,
        status=PickupStopStatus.DELAYED,
    )
    manager_session.add(stop)
    manager_session.flush()

    manager_session.add(
        RouteHistory(
            schedule_id=schedule.id, started_at=now - timedelta(minutes=15), notes="Route started"
        )
    )
    manager_session.add(
        DelayLog(
            stop_id=stop.id,
            worker_id=worker.id,
            reason=DelayReason.WEATHER,
            note="Rain",
        )
    )
    manager_session.add(
        MixedWasteTag(
            stop_id=stop.id,
            worker_id=worker.id,
            severity=WasteSeverity.ROUTINE,
            note="Tag",
        )
    )
    manager_session.commit()

    routes = list_routes(manager_session, [zone.id], zone_code=zone.code, status="DELAYED")
    assert routes.total == 1
    assert routes.delay_logs[0].reason == "WEATHER"

    detail = get_route_detail(manager_session, str(schedule.id), [zone.id])
    assert detail.points[0].label == "Resident Three"
    assert detail.status == "DELAYED"

    workers = list_workers(manager_session, [zone.id], zone_code=zone.code)
    assert workers.total == 1

    reassigned = reassign_worker(
        manager_session,
        str(worker.id),
        type("Req", (), {"zone_id": None, "availability": "AVAILABLE"})(),
        [zone.id],
    )
    assert reassigned.availability == Availability.AVAILABLE
