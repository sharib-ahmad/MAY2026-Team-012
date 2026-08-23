"""Fixtures for SCRUM-178 Civic Reuse Exchange QA."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass

import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.features.reuse.models import ReuseClaim, ReuseImage, ReuseListing
from app.features.users.models import User
from app.models.enums import (
    ReuseCategory,
    ReuseClaimStatus,
    ReuseCondition,
    ReuseStatus,
    Role,
    UserStatus,
)
from app.models.zone import Zone


@dataclass(frozen=True, slots=True)
class ReusePaths:
    """Resolved runtime paths for Civic Reuse Exchange APIs."""

    # Citizen endpoints
    donations: str = "/api/v1/reuse/donations"
    my_donations: str = "/api/v1/reuse/donations/my"
    my_claims: str = "/api/v1/reuse/claims/my"
    shelf: str = "/api/v1/reuse/shelf"
    claim: str = "/api/v1/reuse/donations/{listing_id}/claim"
    withdraw: str = "/api/v1/reuse/donations/{listing_id}/withdraw"

    # Manager endpoints
    pending_donations: str = "/api/v1/reuse/manager/donations/pending"
    all_donations: str = "/api/v1/reuse/manager/donations"
    pending_claims: str = "/api/v1/reuse/manager/claims/pending"
    review_donation: str = "/api/v1/reuse/donations/{listing_id}/review"
    review_claim: str = "/api/v1/reuse/claims/{claim_id}/review"


@pytest.fixture
def reuse_paths() -> ReusePaths:
    return ReusePaths()


# ---------------------------------------------------------------------------
# Zone factories
# ---------------------------------------------------------------------------


@pytest.fixture
def make_zone(db: Session) -> Callable[..., Zone]:
    def _make_zone(*, name: str = "Reuse Ward") -> Zone:
        suffix = uuid.uuid4().hex[:6].upper()
        zone = Zone(code=f"R-{suffix}", name=name)
        db.add(zone)
        db.flush()
        return zone

    return _make_zone


@pytest.fixture
def test_zone(make_zone) -> Zone:
    return make_zone()


@pytest.fixture
def second_zone(make_zone) -> Zone:
    return make_zone(name="Second Reuse Ward")


# ---------------------------------------------------------------------------
# User factories
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
            name=name or f"reuse-{role.value.lower()}-{suffix}",
            email=f"reuse-{suffix}@verdeza.test",
            password_hash=get_password_hash("TestPass123!"),
            phone=f"+1666{int(suffix, 16) % 10_000_000:07d}",
            role=role,
            status=status,
            zone_id=zone.id if zone else None,
        )
        db.add(user)
        db.flush()
        return user

    return _make_user


@pytest.fixture
def donor(make_user, test_zone) -> User:
    return make_user(zone=test_zone, name="QA Donor")


@pytest.fixture
def claimant(make_user, test_zone) -> User:
    return make_user(zone=test_zone, name="QA Claimant")


@pytest.fixture
def second_claimant(make_user, test_zone) -> User:
    return make_user(zone=test_zone, name="QA Claimant B")


@pytest.fixture
def manager(make_user, test_zone, db: Session) -> User:
    mgr = make_user(role=Role.MUNICIPAL_OFFICER, zone=test_zone, name="QA Manager")
    test_zone.manager_id = mgr.id
    db.flush()
    return mgr


@pytest.fixture
def recycler(make_user, test_zone) -> User:
    return make_user(role=Role.RECYCLER, zone=test_zone, name="QA Recycler")


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
# Listing factory
# ---------------------------------------------------------------------------


@pytest.fixture
def make_listing(db: Session) -> Callable[..., ReuseListing]:
    def _make_listing(
        *,
        donor: User,
        zone: Zone | None,
        status: ReuseStatus = ReuseStatus.PENDING_APPROVAL,
        title: str = "QA Reuse Item",
        category: ReuseCategory = ReuseCategory.FURNITURE,
        condition: ReuseCondition = ReuseCondition.GOOD,
        description: str = "A reusable item for QA.",
        images: list[str] | None = None,
        rejection_reason: str | None = None,
    ) -> ReuseListing:
        listing = ReuseListing(
            lister_id=donor.id,
            zone_id=zone.id if zone else None,
            title=title,
            category=category,
            condition=condition,
            description=description,
            status=status,
            rejection_reason=rejection_reason,
        )
        db.add(listing)
        db.flush()
        for order, url in enumerate(images or [], start=1):
            db.add(ReuseImage(listing_id=listing.id, img_url=url, sort_order=order))
        db.flush()
        return listing

    return _make_listing


# ---------------------------------------------------------------------------
# Claim factory
# ---------------------------------------------------------------------------


@pytest.fixture
def make_claim(db: Session) -> Callable[..., ReuseClaim]:
    def _make_claim(
        *,
        listing: ReuseListing,
        claimant: User,
        status: ReuseClaimStatus = ReuseClaimStatus.PENDING,
    ) -> ReuseClaim:
        claim = ReuseClaim(
            listing_id=listing.id,
            claimant_id=claimant.id,
            status=status,
        )
        db.add(claim)
        db.flush()
        return claim

    return _make_claim
