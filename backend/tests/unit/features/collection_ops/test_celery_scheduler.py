from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.core.celery_app import generate_daily_schedules
from app.models.enums import Role, UserStatus


class FakeSession:
    def __init__(self, collectors, pending_requests=None, schedule=None, citizens=None):
        self.collectors = collectors
        self.pending_requests = pending_requests or []
        self.schedule = schedule
        self.citizens = citizens or []
        self.added = []
        self.committed = False
        self.rolled_back = False

    def scalars(self, statement):
        stmt_str = str(statement).lower()
        if "users" in stmt_str or "role" in stmt_str:
            try:
                params = statement.compile().params
                roles = [val for key, val in params.items() if "role" in key]
                if roles:
                    role_val = getattr(roles[0], "value", roles[0])
                    if role_val == Role.COLLECTION_WORKER:
                        return SimpleNamespace(all=lambda: self.collectors)
                    elif role_val == Role.CITIZEN:
                        return SimpleNamespace(all=lambda: self.citizens)
            except Exception:
                pass
            return SimpleNamespace(all=lambda: self.collectors)
        elif "stop" in stmt_str or "delay" in stmt_str or "tag" in stmt_str:
            return SimpleNamespace(all=lambda: [])
        elif "schedule" in stmt_str:
            return SimpleNamespace(all=lambda: [self.schedule] if self.schedule else [])
        else:
            return SimpleNamespace(all=lambda: self.pending_requests)

    def scalar(self, statement):
        # Mocking the schedule query
        return self.schedule

    def add(self, obj):
        self.added.append(obj)

    def add_all(self, objs):
        self.added.extend(objs)

    def flush(self):
        pass

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


@patch("app.core.celery_app.make_engine")
@patch("app.core.celery_app.make_session_factory")
@patch("app.features.collection_ops.router._materialize_assigned_bulk_stops")
def test_generate_daily_schedules_creates_new_schedule(
    mock_materialize, mock_session_factory, mock_engine
):
    collector_id = uuid4()
    zone_id = uuid4()
    collector = SimpleNamespace(
        id=collector_id,
        name="John Collector",
        role=Role.COLLECTION_WORKER,
        status=UserStatus.ACTIVE,
        deleted_at=None,
        zone_id=zone_id,
    )

    fake_session = FakeSession(collectors=[collector], schedule=None)
    mock_session_factory.return_value = lambda: fake_session

    generate_daily_schedules()

    # Verify that a DailyPickupSchedule was created and added
    assert len(fake_session.added) == 1
    schedule = fake_session.added[0]
    assert schedule.collector_id == collector_id
    assert schedule.zone_id == zone_id
    assert schedule.total_stops == 0
    assert schedule.completed_stops == 0
    assert schedule.is_active is True

    # Verify commit was called
    assert fake_session.committed is True
    # Verify materialize was called
    mock_materialize.assert_called_once_with(fake_session, collector)


@patch("app.core.celery_app.make_engine")
@patch("app.core.celery_app.make_session_factory")
@patch("app.features.collection_ops.router._materialize_assigned_bulk_stops")
def test_generate_daily_schedules_reuses_existing_schedule(
    mock_materialize, mock_session_factory, mock_engine
):
    collector_id = uuid4()
    zone_id = uuid4()
    collector = SimpleNamespace(
        id=collector_id,
        name="John Collector",
        role=Role.COLLECTION_WORKER,
        status=UserStatus.ACTIVE,
        deleted_at=None,
        zone_id=zone_id,
    )
    existing_schedule = SimpleNamespace(
        id=uuid4(),
        collector_id=collector_id,
        zone_id=zone_id,
    )

    fake_session = FakeSession(collectors=[collector], schedule=existing_schedule)
    mock_session_factory.return_value = lambda: fake_session

    generate_daily_schedules()

    # Verify that no schedule was added because it already existed
    assert len(fake_session.added) == 0

    # Verify commit was called
    assert fake_session.committed is True
    # Verify materialize was still called
    mock_materialize.assert_called_once_with(fake_session, collector)


@patch("app.core.celery_app.make_engine")
@patch("app.core.celery_app.make_session_factory")
@patch("app.features.collection_ops.router._materialize_assigned_bulk_stops")
def test_generate_daily_schedules_handles_exception_and_rolls_back(
    mock_materialize, mock_session_factory, mock_engine
):
    collector_id = uuid4()
    zone_id = uuid4()
    collector = SimpleNamespace(
        id=collector_id,
        name="John Collector",
        role=Role.COLLECTION_WORKER,
        status=UserStatus.ACTIVE,
        deleted_at=None,
        zone_id=zone_id,
    )

    fake_session = FakeSession(collectors=[collector], schedule=None)
    mock_session_factory.return_value = lambda: fake_session

    # Force an exception in materialize
    mock_materialize.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        generate_daily_schedules()

    # Verify rollback was called and not committed
    assert fake_session.rolled_back is True
    assert fake_session.committed is False


@patch("app.core.celery_app.make_engine")
@patch("app.core.celery_app.make_session_factory")
@patch("app.features.collection_ops.router._materialize_assigned_bulk_stops")
def test_generate_daily_schedules_auto_assigns_pending_requests(
    mock_materialize, mock_session_factory, mock_engine
):
    collector_id = uuid4()
    zone_id = uuid4()
    collector = SimpleNamespace(
        id=collector_id,
        name="John Collector",
        role=Role.COLLECTION_WORKER,
        status=UserStatus.ACTIVE,
        deleted_at=None,
        zone_id=zone_id,
    )

    from app.models.enums import BulkRequestStatus

    pending_request = SimpleNamespace(
        ref_code="BPR-TEST1",
        requester_id=uuid4(),
        zone_id=zone_id,
        status=BulkRequestStatus.PENDING,
        assigned_collector_id=None,
        decided_at=None,
    )

    fake_session = FakeSession(
        collectors=[collector], pending_requests=[pending_request], schedule=None
    )
    mock_session_factory.return_value = lambda: fake_session

    generate_daily_schedules()

    # Verify that the pending request was assigned to the collector
    assert pending_request.assigned_collector_id == collector_id
    assert pending_request.status == BulkRequestStatus.ASSIGNED
    assert pending_request.decided_at is not None

    # Verify notifications were added
    assert len(fake_session.added) == 3  # 1 schedule + 2 notifications
    notifications = [n for n in fake_session.added if hasattr(n, "title")]
    assert len(notifications) == 2
    assert any(n.title == "Bulk pickup assigned" for n in notifications)
    assert any(n.title == "New bulk pickup assignment" for n in notifications)

    # Verify commit was called
    assert fake_session.committed is True


@patch("app.core.celery_app.make_engine")
@patch("app.core.celery_app.make_session_factory")
@patch("app.features.collection_ops.router._materialize_assigned_bulk_stops")
def test_generate_daily_schedules_creates_daily_stops_for_active_citizens(
    mock_materialize, mock_session_factory, mock_engine
):
    collector_id = uuid4()
    zone_id = uuid4()
    collector = SimpleNamespace(
        id=collector_id,
        name="John Collector",
        role=Role.COLLECTION_WORKER,
        status=UserStatus.ACTIVE,
        deleted_at=None,
        zone_id=zone_id,
    )

    citizen_id = uuid4()
    citizen = SimpleNamespace(
        id=citizen_id,
        name="Alice Citizen",
        role=Role.CITIZEN,
        status=UserStatus.ACTIVE,
        deleted_at=None,
        zone_id=zone_id,
        latitude=12.9716,
        longitude=77.5946,
    )

    fake_session = FakeSession(
        collectors=[collector],
        pending_requests=[],
        schedule=None,
        citizens=[citizen],
    )
    mock_session_factory.return_value = lambda: fake_session

    generate_daily_schedules()

    # The session should have added:
    # 1. The DailyPickupSchedule
    # 2. The Pickup (Daily Waste category, 3kg estimated weight)
    # 3. The DailyPickupStop pointing to the Pickup
    assert len(fake_session.added) == 3

    schedule = [x for x in fake_session.added if hasattr(x, "collector_id")][0]
    assert schedule.collector_id == collector_id
    assert schedule.zone_id == zone_id
    assert schedule.total_stops == 1

    pickup = [
        x for x in fake_session.added if hasattr(x, "category") and x.category == "Daily Waste"
    ][0]
    assert pickup.citizen_id == citizen_id
    assert pickup.estimated_weight == 3.0
    assert pickup.ref_code.startswith("COL-DAILY-")

    stop = [x for x in fake_session.added if hasattr(x, "pickup_order")][0]
    assert stop.citizen_id == citizen_id
    assert stop.pickup_order == 1
