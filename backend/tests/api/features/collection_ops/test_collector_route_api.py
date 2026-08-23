from datetime import UTC, datetime

import pytest
from fastapi import status

from app.core.security import create_access_token, get_password_hash
from app.features.collection_ops.models import DailyPickupSchedule, DailyPickupStop, Pickup
from app.features.sorting_guide.models import WasteCategory
from app.features.users.models import User
from app.models.enums import Role, UserStatus


@pytest.mark.integration
@pytest.mark.api
def test_collector_route_only_returns_own_assigned_stops(db_client, db, ward_a):
    """Story 7.2 AC1/AC4: a worker's route/map must only ever show their own
    assigned stops, never another collector's, even within the same ward."""
    category = WasteCategory(code="DRY_ROUTE_TEST", label="Dry Waste", sort_order=1, is_active=True)
    db.add(category)
    db.flush()

    collector_a = User(
        name="Collector A",
        email="collector.a.route@example.com",
        password_hash=get_password_hash("password123"),
        phone="+919876540101",
        role=Role.COLLECTION_WORKER,
        status=UserStatus.ACTIVE,
        zone_id=ward_a.id,
        latitude=26.80,
        longitude=80.90,
    )
    collector_b = User(
        name="Collector B",
        email="collector.b.route@example.com",
        password_hash=get_password_hash("password123"),
        phone="+919876540102",
        role=Role.COLLECTION_WORKER,
        status=UserStatus.ACTIVE,
        zone_id=ward_a.id,
        latitude=26.81,
        longitude=80.91,
    )
    citizen_a = User(
        name="Citizen A",
        email="citizen.a.route@example.com",
        password_hash=get_password_hash("password123"),
        phone="+919876540103",
        role=Role.CITIZEN,
        status=UserStatus.ACTIVE,
        zone_id=ward_a.id,
    )
    citizen_b = User(
        name="Citizen B",
        email="citizen.b.route@example.com",
        password_hash=get_password_hash("password123"),
        phone="+919876540104",
        role=Role.CITIZEN,
        status=UserStatus.ACTIVE,
        zone_id=ward_a.id,
    )
    db.add_all([collector_a, collector_b, citizen_a, citizen_b])
    db.commit()

    pickup_a = Pickup(
        ref_code="PK-ROUTE-A01",
        citizen_id=citizen_a.id,
        zone_id=ward_a.id,
        category=category.code,
        estimated_weight=5,
    )
    pickup_b = Pickup(
        ref_code="PK-ROUTE-B01",
        citizen_id=citizen_b.id,
        zone_id=ward_a.id,
        category=category.code,
        estimated_weight=5,
    )
    db.add_all([pickup_a, pickup_b])
    db.commit()

    schedule_a = DailyPickupSchedule(
        collector_id=collector_a.id,
        zone_id=ward_a.id,
        schedule_date=datetime.now(UTC),
    )
    schedule_b = DailyPickupSchedule(
        collector_id=collector_b.id,
        zone_id=ward_a.id,
        schedule_date=datetime.now(UTC),
    )
    db.add_all([schedule_a, schedule_b])
    db.commit()

    stop_a = DailyPickupStop(
        pickup_id=pickup_a.id,
        schedule_id=schedule_a.id,
        citizen_id=citizen_a.id,
        pickup_order=1,
        latitude=26.85,
        longitude=80.95,
        notes="Stop for Collector A",
    )
    stop_b = DailyPickupStop(
        pickup_id=pickup_b.id,
        schedule_id=schedule_b.id,
        citizen_id=citizen_b.id,
        pickup_order=1,
        latitude=26.86,
        longitude=80.96,
        notes="Stop for Collector B",
    )
    db.add_all([stop_a, stop_b])
    db.commit()

    headers_a = {
        "Authorization": (
            f"Bearer {create_access_token(collector_a.id, token_version=collector_a.token_version)}"
        )
    }
    headers_b = {
        "Authorization": (
            f"Bearer {create_access_token(collector_b.id, token_version=collector_b.token_version)}"
        )
    }

    response_a = db_client.get("/api/v1/collector/route", headers=headers_a)
    response_b = db_client.get("/api/v1/collector/route", headers=headers_b)

    assert response_a.status_code == status.HTTP_200_OK, response_a.text
    assert response_b.status_code == status.HTTP_200_OK, response_b.text

    ref_codes_a = {p["ref_code"] for p in response_a.json()["ordered_pickups"]}
    ref_codes_b = {p["ref_code"] for p in response_b.json()["ordered_pickups"]}

    assert ref_codes_a == {"PK-ROUTE-A01"}
    assert ref_codes_b == {"PK-ROUTE-B01"}
