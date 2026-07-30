import pytest
from sqlalchemy.exc import IntegrityError

from app.features.collection_ops.models import (
    DailyPickupSchedule,
    DailyPickupStop,
    DelayLog,
    Pickup,
)
from app.features.sorting_guide.models import WasteCategory
from app.features.users.models import User
from app.models.enums import DelayReason, Role, UserStatus


@pytest.mark.integration
def test_user_and_waste_category_persists(db, ward_a):
    user = User(
        name="John Doe",
        email="john.doe@example.com",
        password_hash="hashed_password",
        phone="+919876543210",
        role=Role.CITIZEN,
        status=UserStatus.ACTIVE,
        zone_id=ward_a.id,
    )
    db.add(user)

    category = WasteCategory(
        code="DRY_TEST",
        label="Dry Waste",
        sort_order=1,
        is_active=True,
    )
    db.add(category)
    db.flush()

    assert user.id is not None
    assert category.code == "DRY_TEST"


@pytest.mark.integration
def test_delay_log_check_constraint(db, ward_a):
    user = User(
        name="Collector Bob",
        email="bob@example.com",
        password_hash="hashed_password",
        phone="+919876543211",
        role=Role.COLLECTION_WORKER,
        status=UserStatus.ACTIVE,
        zone_id=ward_a.id,
    )
    db.add(user)

    category = WasteCategory(
        code="WET_TEST",
        label="Wet Waste",
        sort_order=2,
        is_active=True,
    )
    db.add(category)
    db.flush()

    pickup = Pickup(
        ref_code="PK-0001",
        resident_id=user.id,
        zone_id=ward_a.id,
        category="WET_TEST",
        estimated_weight=12.5,
    )
    db.add(pickup)
    db.flush()

    schedule = DailyPickupSchedule(
        collector_id=user.id,
        zone_id=ward_a.id,
        schedule_date=pickup.created_at,
    )
    db.add(schedule)
    db.flush()

    stop = DailyPickupStop(
        pickup_id=pickup.id,
        schedule_id=schedule.id,
        resident_id=user.id,
        pickup_order=1,
    )
    db.add(stop)
    db.flush()

    # Attempt to add delay log with reason=OTHER but null note
    delay = DelayLog(
        stop_id=stop.id,
        worker_id=user.id,
        reason=DelayReason.OTHER,
        note=None,
    )
    db.add(delay)

    with pytest.raises(IntegrityError) as captured, db.begin_nested():
        db.flush()

    original = captured.value.orig
    assert original.sqlstate == "23514"
    assert original.diag.constraint_name == "ck_delay_logs_delay_note_mandatory_for_other"
