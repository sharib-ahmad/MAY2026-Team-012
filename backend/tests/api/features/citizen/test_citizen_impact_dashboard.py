"""Dashboard, Sustainability Impact & Gamification API Tests — Stories 8.1, 8.2 (SCRUM-97)."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi import status

from app.features.collection_ops.models import Pickup
from app.features.credits.models import Credit
from app.features.notifications.models import Notification
from app.models.enums import CreditReason, CreditStatus, PickupStatus


@pytest.mark.api
@pytest.mark.integration
class TestCitizenImpactDashboard:
    """Stories 8.1 & 8.2: Dashboard overview, impact analytics, and notifications."""

    def test_dashboard_empty_state(self, db_client, citizen_user, bearer_for):
        """TC-DB01 | Dashboard returns expected zero structure for new resident."""
        response = db_client.get("/api/v1/user/dashboard", headers=bearer_for(citizen_user))

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "pickups" in data
        assert "impact" in data
        assert "queue" in data
        assert "flow" in data
        assert data["impact"]["total_pickups"] == 0
        assert data["impact"]["total_kg_diverted"] == 0

    def test_impact_zero_state(self, db_client, citizen_user, bearer_for):
        """TC-IM01 | Brand new user receives zero state impact data."""
        response = db_client.get("/api/v1/user/impact", headers=bearer_for(citizen_user))

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_pickups"] == 0
        assert data["total_kg_diverted"] == 0.0
        assert data["co2_saved_kg"] == 0.0
        assert data["credits_balance"] == 0.0
        assert data["by_category"] == []
        assert len(data["monthly_trend"]) == 6

    def test_impact_multiple_categories_aggregation(
        self, db_client, db, citizen_user, test_zone, waste_categories, bearer_for
    ):
        """TC-IM02 | Impact correctly aggregates weight, CO2 saved, and credits by category."""
        plastic = waste_categories["PLASTIC"]
        paper = waste_categories["PAPER"]

        p1 = Pickup(
            ref_code="COL-IMP-01",
            citizen_id=citizen_user.id,
            zone_id=test_zone.id,
            category=plastic.code,
            completed_at=datetime.now(UTC) - timedelta(days=5),
            estimated_weight=10.0,
            actual_weight=10.0,
            co2_saved=15.0,
            credits_earned=30.0,
            status=PickupStatus.COMPLETED,
        )
        p2 = Pickup(
            ref_code="COL-IMP-02",
            citizen_id=citizen_user.id,
            zone_id=test_zone.id,
            category=paper.code,
            completed_at=datetime.now(UTC) - timedelta(days=2),
            estimated_weight=20.0,
            actual_weight=20.0,
            co2_saved=24.0,
            credits_earned=40.0,
            status=PickupStatus.COMPLETED,
        )
        db.add_all([p1, p2])

        c1 = Credit(
            user_id=citizen_user.id,
            amount=70.0,
            co2_saved=39.0,
            status=CreditStatus.CONFIRMED,
            reason=CreditReason.PICKUP_RECYCLING,
        )
        db.add(c1)
        db.flush()

        response = db_client.get("/api/v1/user/impact", headers=bearer_for(citizen_user))
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total_pickups"] == 2
        assert data["total_kg_diverted"] == 30.0
        assert data["co2_saved_kg"] == 39.0
        assert data["credits_balance"] == 70.0
        assert len(data["by_category"]) == 2

    def test_impact_badges_progression(
        self, db_client, db, citizen_user, test_zone, waste_categories, bearer_for
    ):
        """TC-IM03 | Verify badges earned progression."""
        plastic = waste_categories["PLASTIC"]

        for i in range(5):
            p = Pickup(
                ref_code=f"COL-BDG-0{i}",
                citizen_id=citizen_user.id,
                zone_id=test_zone.id,
                category=plastic.code,
                completed_at=datetime.now(UTC) - timedelta(days=i + 1),
                estimated_weight=11.0,
                actual_weight=11.0,
                status=PickupStatus.COMPLETED,
            )
            db.add(p)
        db.flush()

        response = db_client.get("/api/v1/user/impact", headers=bearer_for(citizen_user))
        assert response.status_code == status.HTTP_200_OK
        badges = response.json()["badges"]
        badge_dict = {b["code"]: b["earned"] for b in badges}

        assert badge_dict["FIRST_PICKUP"] is True
        assert badge_dict["FIVE_PICKUPS"] is True
        assert badge_dict["FIFTY_KG"] is True

    def test_notifications_list_and_mark_read(self, db_client, db, citizen_user, bearer_for):
        """TC-NF01..02 | Resident lists and marks notification as read."""
        notif = Notification(
            user_id=citizen_user.id,
            title="Pickup Reminder",
            body="Your bulk pickup is scheduled for tomorrow.",
            is_read=False,
        )
        db.add(notif)
        db.flush()

        # List notifications
        list_resp = db_client.get("/api/v1/user/notifications", headers=bearer_for(citizen_user))
        assert list_resp.status_code == status.HTTP_200_OK
        assert len(list_resp.json()) >= 1

        # Mark read
        read_resp = db_client.patch(
            f"/api/v1/user/notifications/{notif.id}/read", headers=bearer_for(citizen_user)
        )
        assert read_resp.status_code == status.HTTP_200_OK
        assert read_resp.json()["is_read"] is True

    def test_citizen_cannot_access_other_citizens_notifications(
        self, db_client, db, citizen_user, second_citizen, bearer_for
    ):
        """TC-NF03 | Data Isolation: Citizen A cannot mark or view Citizen B's notification."""
        notif = Notification(
            user_id=second_citizen.id,
            title="Private Notif",
            body="Secret info for second citizen only",
        )
        db.add(notif)
        db.flush()

        response = db_client.patch(
            f"/api/v1/user/notifications/{notif.id}/read",
            headers=bearer_for(citizen_user),
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
