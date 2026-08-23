"""Public Grievance & Complaint Management API Tests — Stories 2.1, 2.2, 2.3 (SCRUM-97)."""

import pytest
from fastapi import status

from app.features.complaints.models import Ticket
from app.features.notifications.models import Notification
from app.models.enums import TicketStatus, TicketType


@pytest.mark.api
@pytest.mark.integration
class TestCitizenComplaints:
    """Stories 2.1, 2.2, 2.3: Text-based complaint lodging & tracking."""

    def test_create_ticket_happy_path(self, db_client, citizen_user, test_zone, bearer_for):
        """TC-TK01 | Submit complaint ticket → 201 Created."""
        payload = {
            "issue_type": "MISSED_PICKUP",
            "description": "The scheduled morning garbage collection was missed today.",
        }

        response = db_client.post(
            "/api/v1/user/tickets", json=payload, headers=bearer_for(citizen_user)
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["ref_code"].startswith("TK-")
        assert data["status"] == "OPEN"
        assert data["issue_type"] == "MISSED_PICKUP"
        assert data["ward_code"] == test_zone.code

    def test_create_ticket_triggers_manager_notification(
        self, db_client, db, citizen_user, test_zone, manager_user, bearer_for
    ):
        """TC-TK02 | Raising a complaint creates notifications for resident AND ward manager."""
        payload = {
            "issue_type": "OVERFLOW",
            "description": "Overflowing waste bin requiring urgent clearance.",
        }

        response = db_client.post(
            "/api/v1/user/tickets", json=payload, headers=bearer_for(citizen_user)
        )
        assert response.status_code == status.HTTP_201_CREATED
        ref_code = response.json()["ref_code"]

        # Cross-module Manager notification
        manager_notifs = (
            db.query(Notification)
            .filter(Notification.user_id == manager_user.id)
            .order_by(Notification.created_at.desc())
            .all()
        )
        assert any("complaint" in n.title.lower() and ref_code in n.body for n in manager_notifs)

    @pytest.mark.parametrize(
        ("issue_type", "description", "expected_status"),
        [
            (
                "INVALID_ISSUE_TYPE",
                "Valid description text for testing",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ),
            ("MISSED_PICKUP", "Short", status.HTTP_422_UNPROCESSABLE_ENTITY),
            ("OVERFLOW", "a" * 501, status.HTTP_422_UNPROCESSABLE_ENTITY),
        ],
    )
    def test_create_ticket_schema_validation_failures(
        self, db_client, citizen_user, issue_type, description, expected_status, bearer_for
    ):
        """TC-TK03..05 | Invalid issue type or description min/max boundaries fail with 422."""
        payload = {"issue_type": issue_type, "description": description}

        response = db_client.post(
            "/api/v1/user/tickets", json=payload, headers=bearer_for(citizen_user)
        )

        assert response.status_code == expected_status

    def test_citizen_without_ward_cannot_raise_ticket(self, db_client, citizen_no_ward, bearer_for):
        """TC-TK06 | Citizens without a zone_id assigned are blocked from raising tickets (422)."""
        payload = {
            "issue_type": "OVERFLOW",
            "description": "Overflowing bin on street corner requiring pickup.",
        }

        response = db_client.post(
            "/api/v1/user/tickets", json=payload, headers=bearer_for(citizen_no_ward)
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_tickets_returns_user_tickets_with_ward_details(
        self, db_client, db, citizen_user, test_zone, manager_user, bearer_for
    ):
        """TC-TK07 | List complaints populates ward details and manager name."""
        ticket = Ticket(
            ref_code="TK-LISTW01",
            raised_by_id=citizen_user.id,
            zone_id=test_zone.id,
            issue_type=TicketType.OVERFLOW,
            status=TicketStatus.OPEN,
            description="Overflowing community bin near Sector A main entrance.",
        )
        db.add(ticket)
        db.flush()

        response = db_client.get("/api/v1/user/tickets", headers=bearer_for(citizen_user))

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        t = next(item for item in data["tickets"] if item["ref_code"] == "TK-LISTW01")
        assert t["ward_code"] == test_zone.code
        assert t["ward_manager_name"] == manager_user.name
