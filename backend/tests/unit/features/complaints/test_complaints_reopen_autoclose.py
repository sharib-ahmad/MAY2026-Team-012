from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.security import create_access_token
from app.db.session import get_db
from app.features.complaints.models import Ticket
from app.features.complaints.schemas import TicketReopenRequest
from app.features.complaints.service import auto_close_resolved_tickets
from app.features.manager.schemas import WorkerUpdate
from app.features.users.models import User
from app.main import create_app
from app.models.enums import Role, TicketStatus
from app.models.zone import Zone


@pytest.fixture
def test_zone(db):
    zone = Zone(code="TEST-Z", name="Test Zone")
    db.add(zone)
    db.commit()
    return zone


@pytest.fixture
def citizen_user(db, test_zone):
    user = User(
        name="Citizen User",
        email="citizen@example.com",
        phone="+919999999999",
        role=Role.CITIZEN,
        zone_id=test_zone.id,
        password_hash="mock_hash",
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def other_citizen(db, test_zone):
    user = User(
        name="Other User",
        email="other@example.com",
        phone="+918888888888",
        role=Role.CITIZEN,
        zone_id=test_zone.id,
        password_hash="mock_hash",
    )
    db.add(user)
    db.commit()
    return user


def test_resolved_ticket_auto_closure(db, test_zone, citizen_user):
    # 1. Ticket resolved more than 24 hours ago
    t1 = Ticket(
        ref_code="TK-AUTO-1",
        raised_by_id=citizen_user.id,
        zone_id=test_zone.id,
        issue_type="MISSED_PICKUP",
        status=TicketStatus.RESOLVED,
        description="Missed pickup",
        resolved_at=datetime.now(UTC) - timedelta(hours=25),
    )
    # 2. Ticket resolved less than 24 hours ago
    t2 = Ticket(
        ref_code="TK-AUTO-2",
        raised_by_id=citizen_user.id,
        zone_id=test_zone.id,
        issue_type="MISSED_PICKUP",
        status=TicketStatus.RESOLVED,
        description="Missed pickup",
        resolved_at=datetime.now(UTC) - timedelta(hours=10),
    )
    db.add_all([t1, t2])
    db.commit()

    auto_close_resolved_tickets(db)
    db.refresh(t1)
    db.refresh(t2)

    assert t1.status == TicketStatus.CLOSED
    assert t2.status == TicketStatus.RESOLVED


def test_worker_update_validation():
    # Blank name should fail validation
    with pytest.raises(ValidationError):
        WorkerUpdate(name="   ", phone="+919876543210", status="ACTIVE")

    # Blank phone should fail validation
    with pytest.raises(ValidationError):
        WorkerUpdate(name="Worker", phone="   ", status="ACTIVE")

    # Valid name, phone, and DISABLED status should pass
    wu = WorkerUpdate(name="Valid Worker", phone="+919876543210", status="DISABLED")
    assert wu.name == "Valid Worker"
    assert wu.status == "DISABLED"


def test_ticket_reopen_request_validation():
    with pytest.raises(ValidationError):
        TicketReopenRequest(note="   ")

    req = TicketReopenRequest(note="Still not picked up.")
    assert req.note == "Still not picked up."


def test_reopen_api_success(db, test_zone, citizen_user):
    ticket = Ticket(
        ref_code="TK-REOPEN-1",
        raised_by_id=citizen_user.id,
        zone_id=test_zone.id,
        issue_type="MISSED_PICKUP",
        status=TicketStatus.RESOLVED,
        description="Original description",
        resolved_at=datetime.now(UTC) - timedelta(hours=2),
    )
    db.add(ticket)
    db.commit()

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)

    token = create_access_token(citizen_user.id, token_version=citizen_user.token_version)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        f"/api/v1/complaints/{ticket.id}/reopen",
        headers=headers,
        json={"note": "Please look again."},
    )

    assert response.status_code == 200
    db.refresh(ticket)
    assert ticket.status == TicketStatus.OPEN
    assert "Please look again." in ticket.description
    assert ticket.resolved_at is None
    assert ticket.resolved_by_id is None


def test_reopen_api_expired(db, test_zone, citizen_user):
    ticket = Ticket(
        ref_code="TK-REOPEN-EXPIRED",
        raised_by_id=citizen_user.id,
        zone_id=test_zone.id,
        issue_type="MISSED_PICKUP",
        status=TicketStatus.RESOLVED,
        description="Original description",
        resolved_at=datetime.now(UTC) - timedelta(hours=25),
    )
    db.add(ticket)
    db.commit()

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)

    token = create_access_token(citizen_user.id, token_version=citizen_user.token_version)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        f"/api/v1/complaints/{ticket.id}/reopen",
        headers=headers,
        json={"note": "Should fail."},
    )

    assert response.status_code == 409
    db.refresh(ticket)
    assert ticket.status == TicketStatus.CLOSED  # Auto closed!
