"""Shared fixtures for cross-role system journey tests.

Mirrors the user/zone/auth factory pattern already established in
tests/api/features/recycler/conftest.py so these journeys exercise the same
real FastAPI + PostgreSQL stack through the same idioms.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.features.sorting_guide.models import WasteCategory
from app.features.users.models import User
from app.models.enums import Role, UserStatus
from app.models.zone import Zone


@pytest.fixture
def make_zone(db: Session) -> Callable[..., Zone]:
    def _make_zone(*, name: str = "System Journey Zone") -> Zone:
        suffix = uuid.uuid4().hex[:6].upper()
        zone = Zone(code=f"SYS-{suffix}", name=name)
        db.add(zone)
        db.flush()
        return zone

    return _make_zone


@pytest.fixture
def test_zone(make_zone) -> Zone:
    return make_zone()


@pytest.fixture
def make_user(db: Session) -> Callable[..., User]:
    def _make_user(
        *,
        role: Role = Role.CITIZEN,
        zone: Zone | None = None,
        status: UserStatus = UserStatus.ACTIVE,
        name: str | None = None,
    ) -> User:
        suffix = uuid.uuid4().hex[:8]
        user = User(
            name=name or f"sys-{role.value.lower()}-{suffix}",
            email=f"sys-{suffix}@verdeza.test",
            password_hash=get_password_hash("TestPass123!"),
            phone=f"+1888{int(suffix, 16) % 10_000_000:07d}",
            role=role,
            status=status,
            zone_id=zone.id if zone else None,
        )
        db.add(user)
        db.flush()
        return user

    return _make_user


@pytest.fixture
def manager_user(make_user, test_zone, db: Session) -> User:
    mgr = make_user(role=Role.MUNICIPAL_OFFICER, zone=test_zone, name="QA Manager")
    test_zone.manager_id = mgr.id
    db.flush()
    return mgr


@pytest.fixture
def collector_user(make_user, test_zone) -> User:
    return make_user(role=Role.COLLECTION_WORKER, zone=test_zone, name="QA Collector")


@pytest.fixture
def citizen_user(make_user, test_zone) -> User:
    return make_user(role=Role.CITIZEN, zone=test_zone, name="QA Citizen A")


@pytest.fixture
def second_citizen(make_user, test_zone) -> User:
    return make_user(role=Role.CITIZEN, zone=test_zone, name="QA Citizen B")


@pytest.fixture
def bearer_for() -> Callable[[User], dict[str, str]]:
    def _bearer(user: User) -> dict[str, str]:
        token = create_access_token(subject=str(user.id), token_version=user.token_version)
        return {"Authorization": f"Bearer {token}"}

    return _bearer


@pytest.fixture
def waste_category(db: Session) -> WasteCategory:
    cat = db.scalar(select(WasteCategory).where(WasteCategory.code == "PLASTIC"))
    if not cat:
        cat = WasteCategory(code="PLASTIC", label="Plastic Waste")
        db.add(cat)
        db.flush()
    return cat
