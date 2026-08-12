"""Fixtures for SCRUM-194 Recycler Dashboard & Gamification QA."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.features.collection_ops.models import Pickup
from app.features.credits.models import CreditFactor
from app.features.materials.models import Batch
from app.features.sorting_guide.models import WasteCategory
from app.features.users.models import User
from app.models.enums import BatchStatus, PickupStatus, Role, UserStatus
from app.models.zone import Zone


@dataclass(frozen=True, slots=True)
class RecyclerPaths:
    """Resolved runtime paths for Manager & Recycler Batch APIs."""

    # Manager batch routes
    manager_batches: str = "/api/v1/manager/batches"
    manager_recyclers: str = "/api/v1/manager/recyclers"
    manager_assign: str = "/api/v1/manager/batches/{batch_id}/assign"

    # Recycler batch routes
    recycler_batches: str = "/api/v1/recycler/batches"
    recycler_accept: str = "/api/v1/recycler/batches/{batch_id}/accept"
    recycler_reject: str = "/api/v1/recycler/batches/{batch_id}/reject"
    recycler_process: str = "/api/v1/recycler/batches/{batch_id}/process"
    recycler_notifications: str = "/api/v1/recycler/notifications"
    recycler_mark_read: str = "/api/v1/recycler/notifications/{notification_id}/read"
    recycler_mark_all_read: str = "/api/v1/recycler/notifications/read"


@pytest.fixture
def recycler_paths() -> RecyclerPaths:
    return RecyclerPaths()


# ---------------------------------------------------------------------------
# Zone fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def make_zone(db: Session) -> Callable[..., Zone]:
    def _make_zone(*, name: str = "Recycler Zone") -> Zone:
        suffix = uuid.uuid4().hex[:6].upper()
        zone = Zone(code=f"RCY-{suffix}", name=name)
        db.add(zone)
        db.flush()
        return zone

    return _make_zone


@pytest.fixture
def test_zone(make_zone) -> Zone:
    return make_zone()


@pytest.fixture
def second_zone(make_zone) -> Zone:
    return make_zone(name="Second Recycler Zone")


# ---------------------------------------------------------------------------
# User fixtures & factory
# ---------------------------------------------------------------------------


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
            name=name or f"rcy-{role.value.lower()}-{suffix}",
            email=f"rcy-{suffix}@verdeza.test",
            password_hash=get_password_hash("TestPass123!"),
            phone=f"+1777{int(suffix, 16) % 10_000_000:07d}",
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
def recycler_user(make_user, test_zone) -> User:
    return make_user(role=Role.RECYCLER, zone=test_zone, name="QA Recycler A")


@pytest.fixture
def second_recycler(make_user, test_zone) -> User:
    return make_user(role=Role.RECYCLER, zone=test_zone, name="QA Recycler B")


@pytest.fixture
def collector_user(make_user, test_zone) -> User:
    return make_user(role=Role.COLLECTION_WORKER, zone=test_zone, name="QA Collector")


@pytest.fixture
def citizen_user(make_user, test_zone) -> User:
    return make_user(role=Role.CITIZEN, zone=test_zone, name="QA Citizen A")


@pytest.fixture
def second_citizen(make_user, test_zone) -> User:
    return make_user(role=Role.CITIZEN, zone=test_zone, name="QA Citizen B")


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------


@pytest.fixture
def bearer_for() -> Callable[[User], dict[str, str]]:
    def _bearer(user: User) -> dict[str, str]:
        token = create_access_token(subject=str(user.id), token_version=user.token_version)
        return {"Authorization": f"Bearer {token}"}

    return _bearer


# ---------------------------------------------------------------------------
# Reference data fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def waste_category(db: Session) -> WasteCategory:
    cat = db.scalar(select(WasteCategory).where(WasteCategory.code == "PLASTIC"))
    if not cat:
        cat = WasteCategory(
            code="PLASTIC",
            label="Plastic Waste",
        )
        db.add(cat)
        db.flush()
    return cat


@pytest.fixture
def second_waste_category(db: Session) -> WasteCategory:
    cat = db.scalar(select(WasteCategory).where(WasteCategory.code == "PAPER"))
    if not cat:
        cat = WasteCategory(
            code="PAPER",
            label="Paper & Cardboard",
        )
        db.add(cat)
        db.flush()
    return cat


@pytest.fixture
def credit_factor(db: Session, waste_category) -> CreditFactor:
    factor = db.scalar(select(CreditFactor).where(CreditFactor.category == waste_category.code))
    if not factor:
        factor = CreditFactor(
            category=waste_category.code,
            credit_rate=2.5,
            co2_factor=1.8,
        )
        db.add(factor)
        db.flush()
    return factor


# ---------------------------------------------------------------------------
# Domain object factories
# ---------------------------------------------------------------------------


@pytest.fixture
def make_batch(db: Session) -> Callable[..., Batch]:
    def _make_batch(
        *,
        collector: User,
        zone: Zone,
        category: str = "PLASTIC",
        status: BatchStatus = BatchStatus.COLLECTED,
        recycler: User | None = None,
        weight: float = 35.0,
    ) -> Batch:
        existing_count = db.scalar(select(func.count()).select_from(Batch)) or 0
        ref_code = f"BAT-{uuid.uuid4().hex[:4].upper()}-{existing_count + 1:05d}"
        batch = Batch(
            ref_code=ref_code,
            collector_id=collector.id,
            zone_id=zone.id,
            waste_category=category,
            declared_weight=weight,
            status=status,
            destination_recycler_id=recycler.id if recycler else None,
        )
        db.add(batch)
        db.flush()
        return batch

    return _make_batch


@pytest.fixture
def make_pickup(db: Session) -> Callable[..., Pickup]:
    def _make_pickup(
        *,
        citizen: User,
        zone: Zone,
        collector: User | None = None,
        category: str = "PLASTIC",
        status: PickupStatus = PickupStatus.COLLECTED,
        batch: Batch | None = None,
        weight: float = 15.0,
    ) -> Pickup:
        ref_code = f"COL-{uuid.uuid4().hex[:6].upper()}"
        pickup = Pickup(
            ref_code=ref_code,
            citizen_id=citizen.id,
            zone_id=zone.id,
            collector_id=collector.id if collector else None,
            category=category,
            estimated_weight=weight,
            actual_weight=weight,
            status=status,
            batch_id=batch.id if batch else None,
            scheduled_date="2026-08-15",
            time_slot="MORNING",
        )
        db.add(pickup)
        db.flush()
        return pickup

    return _make_pickup
