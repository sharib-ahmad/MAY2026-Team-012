"""Bulk Waste Pickup Scheduling API Tests — Story 1.3 (SCRUM-97)."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status

from app.features.bulk_pickups.models import BulkPickupRequest
from app.features.notifications.models import Notification
from app.models.enums import BulkRequestStatus


@pytest.mark.api
@pytest.mark.integration
class TestCitizenBulkPickups:
    """Story 1.3: Pickup scheduling, listing, tracking & options."""

    def test_create_pickup_happy_path(
        self, db_client, db, citizen_user, test_zone, waste_categories, bearer_for
    ):
        """TC-PU01 | Create pickup with valid payload → 201 Created."""
        payload = {
            "category": "PLASTIC",
            "estimated_weight": 12.5,
            "scheduled_date": (datetime.now(UTC) + timedelta(hours=48)).isoformat(),
            "time_slot": "Morning (8-11)",
            "notes": "Large bulk plastics from spring cleaning",
        }

        response = db_client.post(
            "/api/v1/user/pickups", json=payload, headers=bearer_for(citizen_user)
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["ref_code"].startswith("BPR-")
        assert data["status"] == "PENDING"
        assert data["category"] == "Plastic"
        assert data["estimated_weight"] == 12.5
        assert "W-04" in data["zone_name"]

    def test_create_pickup_triggers_manager_notification(
        self, db_client, db, citizen_user, test_zone, manager_user, waste_categories, bearer_for
    ):
        """TC-PU02 | Bulk pickup creates notifications for resident AND ward manager."""
        payload = {
            "category": "PLASTIC",
            "estimated_weight": 10.0,
            "scheduled_date": (datetime.now(UTC) + timedelta(hours=36)).isoformat(),
            "time_slot": "Morning (8-11)",
        }

        response = db_client.post(
            "/api/v1/user/pickups", json=payload, headers=bearer_for(citizen_user)
        )
        assert response.status_code == status.HTTP_201_CREATED
        ref_code = response.json()["ref_code"]

        # Check manager notification created
        manager_notifs = (
            db.query(Notification)
            .filter(Notification.user_id == manager_user.id)
            .order_by(Notification.created_at.desc())
            .all()
        )
        assert len(manager_notifs) >= 1
        assert any(ref_code in n.body and "bulk pickup" in n.title.lower() for n in manager_notifs)

    def test_create_pickup_invalid_category_returns_422(
        self, db_client, citizen_user, waste_categories, bearer_for
    ):
        """TC-PU03 | Invalid waste category → 422."""
        payload = {
            "category": "NONEXISTENT_CAT",
            "estimated_weight": 5.0,
            "scheduled_date": (datetime.now(UTC) + timedelta(hours=48)).isoformat(),
            "time_slot": "Morning (8-11)",
        }
        response = db_client.post(
            "/api/v1/user/pickups", json=payload, headers=bearer_for(citizen_user)
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_pickup_less_than_24h_notice_returns_422(
        self, db_client, citizen_user, waste_categories, bearer_for
    ):
        """TC-PU04 | Scheduled date < 24 hours from now → 422."""
        payload = {
            "category": "PLASTIC",
            "estimated_weight": 3.0,
            "scheduled_date": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            "time_slot": "Morning (8-11)",
        }
        response = db_client.post(
            "/api/v1/user/pickups", json=payload, headers=bearer_for(citizen_user)
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_citizen_without_ward_cannot_schedule_pickup(
        self, db_client, citizen_no_ward, waste_categories, bearer_for
    ):
        """TC-PU05 | Citizens without a zone_id assigned cannot schedule pickups (422)."""
        payload = {
            "category": "PLASTIC",
            "estimated_weight": 5.0,
            "scheduled_date": (datetime.now(UTC) + timedelta(hours=48)).isoformat(),
            "time_slot": "Morning (8-11)",
        }

        response = db_client.post(
            "/api/v1/user/pickups", json=payload, headers=bearer_for(citizen_no_ward)
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_pickups_returns_resident_pickups(
        self, db_client, db, citizen_user, test_zone, waste_categories, bearer_for
    ):
        """TC-PU06 | List pickups returns user's requests."""
        bpr = BulkPickupRequest(
            ref_code="BPR-PU07TEST",
            requester_id=citizen_user.id,
            zone_id=test_zone.id,
            category="PAPER",
            requested_date=datetime.now(UTC) + timedelta(days=3),
            estimated_weight=6.0,
            time_slot="Midday (11-2)",
            status=BulkRequestStatus.PENDING,
        )
        db.add(bpr)
        db.flush()

        response = db_client.get("/api/v1/user/pickups", headers=bearer_for(citizen_user))

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        assert any(p["ref_code"] == "BPR-PU07TEST" for p in data["pickups"])

    def test_cancel_pending_pickup_succeeds(
        self, db_client, db, citizen_user, test_zone, waste_categories, bearer_for
    ):
        """TC-PU07 | Cancel PENDING pickup → status=CANCELLED."""
        bpr = BulkPickupRequest(
            ref_code="BPR-CANCEL01",
            requester_id=citizen_user.id,
            zone_id=test_zone.id,
            category="PLASTIC",
            requested_date=datetime.now(UTC) + timedelta(days=3),
            estimated_weight=4.0,
            status=BulkRequestStatus.PENDING,
        )
        db.add(bpr)
        db.flush()

        response = db_client.patch(
            f"/api/v1/user/pickups/{bpr.id}/cancel", headers=bearer_for(citizen_user)
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "CANCELLED"

    def test_cancel_nonexistent_pickup_returns_404(self, db_client, citizen_user, bearer_for):
        """TC-PU08 | Cancel non-existent pickup ID → 404."""
        fake_id = uuid.uuid4()
        response = db_client.patch(
            f"/api/v1/user/pickups/{fake_id}/cancel", headers=bearer_for(citizen_user)
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_citizen_cannot_cancel_other_citizens_pickup(
        self,
        db_client,
        db,
        citizen_user,
        second_citizen,
        second_zone,
        waste_categories,
        bearer_for,
    ):
        """TC-PU09 | Data Isolation: Citizen A cannot cancel Citizen B's pickup request."""
        bpr = BulkPickupRequest(
            ref_code="BPR-SECRET01",
            requester_id=second_citizen.id,
            zone_id=second_zone.id,
            category="PLASTIC",
            requested_date=datetime.now(UTC) + timedelta(days=3),
            estimated_weight=10.0,
            status=BulkRequestStatus.PENDING,
        )
        db.add(bpr)
        db.flush()

        response = db_client.patch(
            f"/api/v1/user/pickups/{bpr.id}/cancel",
            headers=bearer_for(citizen_user),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert bpr.status == BulkRequestStatus.PENDING

    def test_pickup_tracking_happy_path(
        self, db_client, db, citizen_user, test_zone, waste_categories, bearer_for
    ):
        """TC-PU10 | Track valid pickup → tracking object with timeline."""
        bpr = BulkPickupRequest(
            ref_code="BPR-TRACK001",
            requester_id=citizen_user.id,
            zone_id=test_zone.id,
            category="PLASTIC",
            requested_date=datetime.now(UTC) + timedelta(days=3),
            estimated_weight=5.0,
            status=BulkRequestStatus.PENDING,
        )
        db.add(bpr)
        db.flush()

        response = db_client.get(
            f"/api/v1/user/pickups/{bpr.id}/tracking", headers=bearer_for(citizen_user)
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["ref_code"] == "BPR-TRACK001"
        assert len(data["timeline"]) >= 1

    def test_citizen_cannot_track_other_citizens_pickup(
        self,
        db_client,
        db,
        citizen_user,
        second_citizen,
        second_zone,
        waste_categories,
        bearer_for,
    ):
        """TC-PU11 | Data Isolation: Citizen A cannot view Citizen B's pickup tracking."""
        bpr = BulkPickupRequest(
            ref_code="BPR-SECRET02",
            requester_id=second_citizen.id,
            zone_id=second_zone.id,
            category="PAPER",
            requested_date=datetime.now(UTC) + timedelta(days=3),
            estimated_weight=5.0,
            status=BulkRequestStatus.PENDING,
        )
        db.add(bpr)
        db.flush()

        response = db_client.get(
            f"/api/v1/user/pickups/{bpr.id}/tracking",
            headers=bearer_for(citizen_user),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_pickup_options_excludes_inactive_categories(
        self, db_client, citizen_user, waste_categories, bearer_for
    ):
        """TC-PU12 | GET /api/v1/user/pickup-options returns active waste categories."""
        response = db_client.get("/api/v1/user/pickup-options", headers=bearer_for(citizen_user))

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        codes = [cat["code"] for cat in data["categories"]]

        assert "PLASTIC" in codes
        assert "PAPER" in codes
        assert "INACTIVE_CAT" not in codes
