"""Focused fixtures for SCRUM-97 Citizen / Resident API QA."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.features.users.models import User
from app.models.enums import Role, UserStatus
from app.models.zone import Zone


@dataclass(frozen=True, slots=True)
class CitizenPaths:
    """Resolved runtime paths plus canonical paths for Citizen APIs."""

    pickups: str
    cancel_pickup: str
    tracking: str
    pickup_options: str
    complaints: str
    notifications: str
    mark_notification: str
    dashboard: str
    impact: str
    daily_schedules: str


@pytest.fixture
def citizen_paths(app_test) -> CitizenPaths:
    return CitizenPaths(
        pickups="/api/v1/user/pickups",
        cancel_pickup="/api/v1/user/pickups/{pickup_id}/cancel",
        tracking="/api/v1/user/pickups/{pickup_id}/tracking",
        pickup_options="/api/v1/user/pickup-options",
        complaints="/api/v1/user/tickets",
        notifications="/api/v1/user/notifications",
        mark_notification="/api/v1/user/notifications/{notification_id}/read",
        dashboard="/api/v1/user/dashboard",
        impact="/api/v1/user/impact",
        daily_schedules="/api/v1/user/daily-pickup-schedules",
    )


def auth_headers(user: User) -> dict[str, str]:
    """Generate Bearer Authorization header for test requests."""
    token = create_access_token(user.id, token_version=user.token_version)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def make_user(db: Session) -> Callable[..., User]:
    """Create a persisted user with unique safe defaults."""

    def _make_user(
        *,
        name: str = "QA Citizen",
        email: str | None = None,
        phone: str | None = None,
        password: str = "StrongPass123!",
        role: Role = Role.CITIZEN,
        status: UserStatus = UserStatus.ACTIVE,
        zone: Zone | None = None,
        deleted: bool = False,
    ) -> User:
        suffix = uuid.uuid4().hex
        user = User(
            name=name,
            email=email or f"qa-citizen-{suffix}@example.com",
            phone=phone or f"+91{uuid.uuid4().int % 10**10:010d}",
            password_hash=get_password_hash(password),
            role=role,
            status=status,
            zone_id=zone.id if zone else None,
            deleted_at=datetime.now(UTC) if deleted else None,
            latitude=28.6139,
            longitude=77.2090,
        )
        db.add(user)
        db.flush()
        return user

    return _make_user


@pytest.fixture
def bearer_for() -> Callable[[User], dict[str, str]]:
    """Create a Bearer header for a persisted user."""

    def _bearer_for(user: User) -> dict[str, str]:
        return auth_headers(user)

    return _bearer_for


@pytest.fixture
def test_zone(db) -> Zone:
    """Create a primary test ward (zone)."""
    zone = Zone(name="Ward Four", code="W-04", sectors="Sector A, Sector B")
    db.add(zone)
    db.flush()
    return zone


@pytest.fixture
def second_zone(db) -> Zone:
    """Create a secondary test ward for isolation testing."""
    zone = Zone(name="Ward Five", code="W-05", sectors="Sector C")
    db.add(zone)
    db.flush()
    return zone


@pytest.fixture
def citizen_user(make_user: Callable[..., User], test_zone: Zone) -> User:
    """Primary authenticated citizen user."""
    return make_user(
        name="Ananya Sharma",
        email="ananya.sharma@example.com",
        phone="+919811000001",
        role=Role.CITIZEN,
        zone=test_zone,
    )


@pytest.fixture
def second_citizen(make_user: Callable[..., User], second_zone: Zone) -> User:
    """Secondary citizen user for cross-tenant isolation testing."""
    return make_user(
        name="Rohan Verma",
        email="rohan.verma@example.com",
        phone="+919822000002",
        role=Role.CITIZEN,
        zone=second_zone,
    )


@pytest.fixture
def citizen_no_ward(make_user: Callable[..., User]) -> User:
    """Citizen user without an assigned ward."""
    return make_user(
        name="Wardless Citizen",
        email="noward@example.com",
        phone="+919833000003",
        role=Role.CITIZEN,
        zone=None,
    )


@pytest.fixture
def officer_user(make_user: Callable[..., User], test_zone: Zone) -> User:
    """Municipal Officer (non-citizen) for role authorization checks."""
    return make_user(
        name="Officer Rajesh",
        email="officer.rajesh@example.com",
        phone="+919844000004",
        role=Role.MUNICIPAL_OFFICER,
        zone=test_zone,
    )


@pytest.fixture
def collector_user(make_user: Callable[..., User], test_zone: Zone) -> User:
    """Collection Worker (non-citizen) for role authorization checks."""
    return make_user(
        name="Collector Vikram",
        email="collector.vikram@example.com",
        phone="+919855000005",
        role=Role.COLLECTION_WORKER,
        zone=test_zone,
    )


@pytest.fixture
def manager_user(make_user: Callable[..., User], test_zone: Zone, db: Session) -> User:
    """Ward Manager user assigned to test_zone."""
    manager = make_user(
        name="Ward Four Manager",
        email="manager.w04@example.com",
        phone="+919866000006",
        role=Role.MUNICIPAL_OFFICER,
        zone=test_zone,
    )
    test_zone.manager_id = manager.id
    db.flush()
    return manager


@pytest.fixture
def waste_categories(db) -> dict:
    """Seed standard waste categories."""
    from app.features.sorting_guide.models import WasteCategory

    categories = [
        WasteCategory(code="PLASTIC", label="Plastic", sort_order=1, is_active=True),
        WasteCategory(code="PAPER", label="Paper & Cardboard", sort_order=2, is_active=True),
        WasteCategory(code="METAL", label="Metals", sort_order=3, is_active=True),
        WasteCategory(code="GLASS", label="Glass Bottles", sort_order=4, is_active=True),
        WasteCategory(
            code="INACTIVE_CAT", label="Deprecated Category", sort_order=99, is_active=False
        ),
    ]
    for cat in categories:
        db.add(cat)
    db.flush()
    return {cat.code: cat for cat in categories}


def _assert_safe_public_body(response) -> None:
    text = response.text.lower()
    forbidden = (
        "password_hash",
        "token_version",
        "deleted_at",
        "traceback",
        "sqlalchemy",
        "psycopg",
        "constraint",
        "secret_key",
    )
    for term in forbidden:
        assert term not in text


def _assert_safe_error(response, expected_status: int, expected_code: str | None = None) -> dict:
    assert response.status_code == expected_status, response.text
    body = response.json()
    assert set(body) in ({"error"}, {"detail"}) or "error" in body or "detail" in body
    _assert_safe_public_body(response)
    return body


@pytest.fixture
def assert_safe_public_body():
    return _assert_safe_public_body


@pytest.fixture
def assert_safe_error():
    return _assert_safe_error
