"""Daily Collection Schedules & Route Tracking API Tests — Story 1.1 (SCRUM-97)."""

from datetime import UTC, datetime

import pytest
from fastapi import status

from app.features.collection_ops.models import DailyPickupSchedule, DailyPickupStop, Pickup
from app.models.enums import PickupStatus, PickupStopStatus


@pytest.mark.api
@pytest.mark.integration
class TestCitizenSchedules:
    """Story 1.1: Static route schedule look-up & daily pickup queue tracking."""

    def test_daily_pickup_schedule_queue_tracking_journey(
        self, db_client, db, citizen_user, test_zone, collector_user, waste_categories, bearer_for
    ):
        """TC-SC01 | Resident daily collection schedule & queue tracking integration."""
        today = datetime.now(UTC).replace(hour=8, minute=0, second=0, microsecond=0)

        schedule = DailyPickupSchedule(
            collector_id=collector_user.id,
            zone_id=test_zone.id,
            schedule_date=today,
            total_stops=3,
            completed_stops=1,
            is_active=True,
        )
        db.add(schedule)
        db.flush()

        pickup = Pickup(
            ref_code="COL-QUEUE-01",
            citizen_id=citizen_user.id,
            zone_id=test_zone.id,
            category="PAPER",
            estimated_weight=5.0,
            status=PickupStatus.SCHEDULED,
        )
        db.add(pickup)
        db.flush()

        stop = DailyPickupStop(
            schedule_id=schedule.id,
            pickup_id=pickup.id,
            citizen_id=citizen_user.id,
            pickup_order=2,
            status=PickupStopStatus.PENDING,
            latitude=28.6139,
            longitude=77.2090,
            notes="Gate 3 entry",
        )
        db.add(stop)
        db.flush()

        # Check list_daily_pickup_schedules
        schedules_resp = db_client.get(
            "/api/v1/user/daily-pickup-schedules", headers=bearer_for(citizen_user)
        )
        assert schedules_resp.status_code == status.HTTP_200_OK
        s_data = schedules_resp.json()
        assert len(s_data) >= 1
        assert s_data[0]["collector_name"] == collector_user.name
        assert s_data[0]["pickup_order"] == 2
        assert s_data[0]["completed_stops"] == 1
