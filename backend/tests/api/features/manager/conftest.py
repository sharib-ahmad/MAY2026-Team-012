"""Focused fixtures for SCRUM-174 manager API QA."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.db.session import get_db
from app.features.bulk_pickups.models import BulkPickupRequest
from app.features.complaints.models import Ticket
from app.features.notifications.models import Notification
from app.features.sorting_guide.models import WasteCategory
from app.features.users.models import User
from app.models.enums import (
    BulkRequestStatus,
    Role,
    TicketStatus,
    TicketType,
    UserStatus,
)
from app.models.zone import Zone


@dataclass(frozen=True, slots=True)
class ManagerPaths:
    """Runtime paths introduced or used by the manager feature."""

    dashboard: str = "/api/v1/manager/dashboard"
    notifications_read: str = "/api/v1/manager/notifications/read"
    ticket_update: str = "/api/v1/manager/tickets/{ticket_id}"
    bulk_assign: str = "/api/v1/manager/bulk-pickups/{request_id}/assign"
    worker_update: str = "/api/v1/manager/workers/{worker_id}"
    worker_delete: str = "/api/v1/manager/workers/{worker_id}"
    me: str = "/api/v1/me"


@pytest.fixture
def db_client_no_raise(app_test, db):
    """HTTP client that returns the registered 500 response for failure-injection tests."""

    app_test.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app_test, raise_server_exceptions=False) as client:
            yield client
    finally:
        app_test.dependency_overrides.pop(get_db, None)


@pytest.fixture
def manager_paths(app_test) -> ManagerPaths:
    routes = {
        (method, route.path)
        for route in app_test.routes
        for method in getattr(route, "methods", set())
    }
    me_path = "/api/v1/auth/me" if ("GET", "/api/v1/auth/me") in routes else "/api/v1/me"
    return ManagerPaths(me=me_path)


@pytest.fixture
def make_zone(db: Session) -> Callable[..., Zone]:
    """Create a persisted ward with a unique canonical code."""

    def _make_zone(*, code: str | None = None, name: str = "QA Ward") -> Zone:
        suffix = uuid.uuid4().hex[:6].upper()
        zone = Zone(code=code or f"W-{suffix}", name=name)
        db.add(zone)
        db.flush()
        return zone

    return _make_zone


@pytest.fixture
def make_user(db: Session) -> Callable[..., User]:
    """Create a persisted user with unique safe defaults."""

    def _make_user(
        *,
        name: str = "QA User",
        email: str | None = None,
        phone: str | None = None,
        password: str = "StrongPass123!",
        role: Role = Role.CITIZEN,
        status: UserStatus = UserStatus.ACTIVE,
        zone: Zone | None = None,
        token_version: int = 1,
        deleted: bool = False,
    ) -> User:
        suffix = uuid.uuid4().hex
        user = User(
            name=name,
            email=email or f"qa-{suffix}@example.com",
            phone=phone or f"+91{uuid.uuid4().int % 10**10:010d}",
            password_hash=get_password_hash(password),
            role=role,
            status=status,
            zone_id=zone.id if zone else None,
            token_version=token_version,
            deleted_at=datetime.now(UTC) if deleted else None,
        )
        db.add(user)
        db.flush()
        return user

    return _make_user


@pytest.fixture
def bearer_for() -> Callable[[User], dict[str, str]]:
    """Return a Bearer header for a persisted user."""

    def _bearer_for(user: User) -> dict[str, str]:
        token = create_access_token(user.id, token_version=user.token_version)
        return {"Authorization": f"Bearer {token}"}

    return _bearer_for


@pytest.fixture
def manager_ward(make_zone: Callable[..., Zone]) -> Zone:
    return make_zone(code="W-21", name="Manager Ward")


@pytest.fixture
def other_ward(make_zone: Callable[..., Zone]) -> Zone:
    return make_zone(code="W-22", name="Other Ward")


@pytest.fixture
def manager_user(db: Session, make_user: Callable[..., User], manager_ward: Zone) -> User:
    manager = make_user(
        name="QA Municipal Officer",
        email="qa.manager@example.com",
        phone="+919876540001",
        role=Role.MUNICIPAL_OFFICER,
        zone=manager_ward,
    )
    manager_ward.manager_id = manager.id
    db.flush()
    return manager


@pytest.fixture
def manager_without_wards(make_user: Callable[..., User]) -> User:
    return make_user(
        name="QA Unassigned Officer",
        email="qa.unassigned.manager@example.com",
        phone="+919876540002",
        role=Role.MUNICIPAL_OFFICER,
    )


@pytest.fixture
def resident_user(make_user: Callable[..., User], manager_ward: Zone) -> User:
    return make_user(
        name="QA Resident",
        role=Role.CITIZEN,
        zone=manager_ward,
    )


@pytest.fixture
def worker_user(make_user: Callable[..., User], manager_ward: Zone) -> User:
    return make_user(
        name="QA Collection Worker",
        role=Role.COLLECTION_WORKER,
        zone=manager_ward,
    )


@pytest.fixture
def waste_category(db: Session) -> WasteCategory:
    category = db.get(WasteCategory, "DRY")
    if category is None:
        category = WasteCategory(code="DRY", label="Dry Waste", sort_order=1)
        db.add(category)
        db.flush()
    return category


@pytest.fixture
def make_ticket(db: Session) -> Callable[..., Ticket]:
    """Create a persisted complaint ticket."""

    def _make_ticket(
        *,
        raised_by: User,
        zone: Zone,
        status: TicketStatus = TicketStatus.OPEN,
        issue_type: TicketType = TicketType.MISSED_PICKUP,
        description: str = "Missed pickup reported for the assigned ward.",
        resolution_notes: str | None = None,
        created_at: datetime | None = None,
    ) -> Ticket:
        ticket = Ticket(
            ref_code=f"TK-{uuid.uuid4().hex[:8].upper()}",
            raised_by_id=raised_by.id,
            zone_id=zone.id,
            issue_type=issue_type,
            status=status,
            description=description,
            resolution_notes=resolution_notes,
        )
        if created_at is not None:
            ticket.created_at = created_at
        db.add(ticket)
        db.flush()
        return ticket

    return _make_ticket


@pytest.fixture
def make_bulk_request(
    db: Session,
    waste_category: WasteCategory,
) -> Callable[..., BulkPickupRequest]:
    """Create a persisted bulk-pickup request."""

    def _make_bulk_request(
        *,
        requester: User,
        zone: Zone,
        status: BulkRequestStatus = BulkRequestStatus.PENDING,
        requested_date: datetime | None = None,
        assigned_collector: User | None = None,
    ) -> BulkPickupRequest:
        request = BulkPickupRequest(
            ref_code=f"BPR-{uuid.uuid4().hex[:8].upper()}",
            requester_id=requester.id,
            zone_id=zone.id,
            category=waste_category.code,
            requested_date=requested_date or datetime.now(UTC) + timedelta(days=2),
            estimated_weight=25,
            time_slot="MORNING",
            notes="QA bulk pickup request",
            status=status,
            assigned_collector_id=(assigned_collector.id if assigned_collector else None),
        )
        db.add(request)
        db.flush()
        return request

    return _make_bulk_request


@pytest.fixture
def make_notification(db: Session) -> Callable[..., Notification]:
    """Create a persisted notification."""

    def _make_notification(
        *,
        user: User,
        title: str = "QA Notification",
        body: str = "QA notification body",
        is_read: bool = False,
    ) -> Notification:
        notification = Notification(
            user_id=user.id,
            title=title,
            body=body,
            is_read=is_read,
        )
        db.add(notification)
        db.flush()
        return notification

    return _make_notification


def _assert_safe_public_body(response) -> None:
    text = response.text.lower()
    forbidden = (
        "password_hash",
        "token_version",
        "deleted_at",
        "secret_key",
        "traceback",
        "sqlalchemy",
        "psycopg",
        "constraint",
    )
    for term in forbidden:
        assert term not in text


def _assert_safe_error(response, expected_status: int, expected_code: str) -> dict:
    assert response.status_code == expected_status, response.text
    body = response.json()
    assert set(body) == {"error"}
    error = body["error"]
    assert {"code", "message", "request_id"} <= set(error)
    assert error["code"] == expected_code
    assert response.headers.get("X-Request-ID") == error["request_id"]
    _assert_safe_public_body(response)
    return error


@pytest.fixture
def assert_safe_public_body():
    return _assert_safe_public_body


@pytest.fixture
def assert_safe_error():
    return _assert_safe_error
