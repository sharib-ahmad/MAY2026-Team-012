"""Cross-role system journey for daily waste collection.

Exercises the collection lifecycle through the real FastAPI application and a
disposable PostgreSQL database: a collection worker completes their actually
assigned stop through the real endpoint, and the citizen who owns that
pickup reads their own daily collection schedule back through their real API
and sees it reflected as collected.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from app.features.collection_ops.models import DailyPickupSchedule, DailyPickupStop, Pickup
from app.models.enums import PickupStatus, PickupStopStatus


@pytest.mark.system
def test_collection_journey_flow(
    db_client,
    test_zone,
    citizen_user,
    collector_user,
    waste_category,
    bearer_for,
    db: Session,
):
    headers_collector = bearer_for(collector_user)
    headers_citizen = bearer_for(citizen_user)

    # ------- Setup: a real assigned stop on the collector's schedule -------
    pickup = Pickup(
        ref_code=f"COL-{uuid.uuid4().hex[:6].upper()}",
        citizen_id=citizen_user.id,
        collector_id=collector_user.id,
        zone_id=test_zone.id,
        category=waste_category.code,
        estimated_weight=10.0,
        status=PickupStatus.ASSIGNED,
        scheduled_date=datetime.now(UTC),
        time_slot="MORNING",
    )
    db.add(pickup)
    db.flush()

    schedule = DailyPickupSchedule(
        collector_id=collector_user.id,
        zone_id=test_zone.id,
        schedule_date=datetime.now(UTC),
        total_stops=1,
    )
    db.add(schedule)
    db.flush()

    stop = DailyPickupStop(
        pickup_id=pickup.id,
        schedule_id=schedule.id,
        citizen_id=citizen_user.id,
        pickup_order=1,
        status=PickupStopStatus.PENDING,
    )
    db.add(stop)
    db.commit()

    # ------- Step 1: Collector completes the actual assigned stop -------
    complete_resp = db_client.post(
        f"/api/v1/collector/stops/{stop.id}/complete",
        headers=headers_collector,
    )
    assert complete_resp.status_code == status.HTTP_200_OK, (
        f"Step 1 (complete) failed: {complete_resp.text}"
    )
    assert complete_resp.json()["status"] == "COLLECTED"

    # ------- Step 2: Citizen reads their own daily collection schedule -------
    schedule_resp = db_client.get("/api/v1/user/daily-pickup-schedules", headers=headers_citizen)
    assert schedule_resp.status_code == status.HTTP_200_OK

    # ------- Step 3: The schedule reflects that stop as collected -------
    entries = [e for e in schedule_resp.json() if e["schedule_id"] == str(schedule.id)]
    assert len(entries) == 1, "Citizen should see exactly their own scheduled stop"
    assert entries[0]["stop_status"] == "COLLECTED"
    assert entries[0]["completed_stops"] == 1
