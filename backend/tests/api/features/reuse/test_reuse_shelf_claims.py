"""Community Shelf and claim lifecycle tests for SCRUM-178 Reuse QA.

Covers: shelf display, search/category filters, self-listing exclusion,
claim creation, duplicate claim prevention, self-claim prevention,
non-claimable status enforcement, claim listing, and 404 cases.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.notifications.models import Notification
from app.features.reuse.models import ReuseClaim
from app.models.enums import ReuseCategory, ReuseClaimStatus, ReuseStatus

# ---------------------------------------------------------------------------
# REU-S01 | Shelf excludes own listings
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_shelf_excludes_own_listings(
    db_client, reuse_paths, donor, claimant, bearer_for, make_listing, test_zone
):
    """REU-S01 | Shelf hides current user's own listings."""
    own = make_listing(
        donor=claimant,
        zone=test_zone,
        title="My Chair",
        status=ReuseStatus.AVAILABLE,
    )
    other = make_listing(
        donor=donor,
        zone=test_zone,
        title="Someone's Desk",
        status=ReuseStatus.AVAILABLE,
    )

    response = db_client.get(reuse_paths.shelf, headers=bearer_for(claimant))
    assert response.status_code == status.HTTP_200_OK
    ids = {item["id"] for item in response.json()}
    assert str(own.id) not in ids, "Own listing should be excluded from shelf"
    assert str(other.id) in ids


# ---------------------------------------------------------------------------
# REU-S02 | Shelf search and category filter
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_shelf_search_and_category_filter(
    db_client, reuse_paths, donor, claimant, bearer_for, make_listing, test_zone
):
    """REU-S02 | Shelf search + category filtering works together."""
    furniture = make_listing(
        donor=donor,
        zone=test_zone,
        title="Blue Chair",
        category=ReuseCategory.FURNITURE,
        status=ReuseStatus.AVAILABLE,
    )
    book = make_listing(
        donor=donor,
        zone=test_zone,
        title="Old Book",
        category=ReuseCategory.BOOKS,
        status=ReuseStatus.AVAILABLE,
    )

    # Unfiltered — should see both
    response = db_client.get(reuse_paths.shelf, headers=bearer_for(claimant))
    assert response.status_code == status.HTTP_200_OK
    ids = {item["id"] for item in response.json()}
    assert str(furniture.id) in ids
    assert str(book.id) in ids

    # Category filter
    response = db_client.get(
        reuse_paths.shelf,
        params={"category": "FURNITURE"},
        headers=bearer_for(claimant),
    )
    assert response.status_code == status.HTTP_200_OK
    ids = {item["id"] for item in response.json()}
    assert str(furniture.id) in ids
    assert str(book.id) not in ids

    # Search filter
    response = db_client.get(
        reuse_paths.shelf,
        params={"search": "blue"},
        headers=bearer_for(claimant),
    )
    ids = {item["id"] for item in response.json()}
    assert str(furniture.id) in ids
    assert str(book.id) not in ids

    # Combined filter
    response = db_client.get(
        reuse_paths.shelf,
        params={"search": "blue", "category": "FURNITURE"},
        headers=bearer_for(claimant),
    )
    assert [item["id"] for item in response.json()] == [str(furniture.id)]


# ---------------------------------------------------------------------------
# REU-S03 | Shelf only shows AVAILABLE listings
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_shelf_only_shows_available_listings(
    db_client, reuse_paths, donor, claimant, bearer_for, make_listing, test_zone
):
    """REU-S03 | Non-AVAILABLE listings are hidden from shelf."""
    available = make_listing(
        donor=donor,
        zone=test_zone,
        title="Available Item",
        status=ReuseStatus.AVAILABLE,
    )
    make_listing(
        donor=donor,
        zone=test_zone,
        title="Pending Item",
        status=ReuseStatus.PENDING_APPROVAL,
    )
    make_listing(
        donor=donor,
        zone=test_zone,
        title="Completed Item",
        status=ReuseStatus.COMPLETED,
    )

    response = db_client.get(reuse_paths.shelf, headers=bearer_for(claimant))
    ids = {item["id"] for item in response.json()}
    assert str(available.id) in ids
    assert len(ids) == 1


# ---------------------------------------------------------------------------
# REU-C01 | Claim available item
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_claim_available_item(
    db_client,
    reuse_paths,
    donor,
    claimant,
    bearer_for,
    make_listing,
    db: Session,
    test_zone,
    manager,
):
    """REU-C01 | Claim available listing → CLAIM_REQUESTED, claim created."""
    listing = make_listing(donor=donor, zone=test_zone, status=ReuseStatus.AVAILABLE)
    response = db_client.post(
        reuse_paths.claim.format(listing_id=listing.id),
        headers=bearer_for(claimant),
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "CLAIM_REQUESTED"

    db.refresh(listing)
    assert listing.status == ReuseStatus.CLAIM_PENDING

    claim = db.scalar(select(ReuseClaim).where(ReuseClaim.listing_id == listing.id))
    assert claim is not None
    assert claim.claimant_id == claimant.id
    assert claim.status == ReuseClaimStatus.PENDING

    # Manager should be notified
    mgr_notifs = db.scalars(select(Notification).where(Notification.user_id == manager.id)).all()
    assert any(n.title == "New claim request" for n in mgr_notifs)


# ---------------------------------------------------------------------------
# REU-C02 | Cannot claim own listing
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.security
def test_cannot_claim_own_listing(
    db_client, reuse_paths, donor, bearer_for, make_listing, test_zone
):
    """REU-C02 | Self-claim blocked with 409."""
    listing = make_listing(donor=donor, zone=test_zone, status=ReuseStatus.AVAILABLE)
    response = db_client.post(
        reuse_paths.claim.format(listing_id=listing.id),
        headers=bearer_for(donor),
    )
    assert response.status_code == status.HTTP_409_CONFLICT


# ---------------------------------------------------------------------------
# REU-C03 | Cannot claim same item twice
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_cannot_claim_item_twice(
    db_client, reuse_paths, donor, claimant, bearer_for, make_listing, test_zone
):
    """REU-C03 | Duplicate pending claim blocked with 409."""
    listing = make_listing(donor=donor, zone=test_zone, status=ReuseStatus.AVAILABLE)
    first = db_client.post(
        reuse_paths.claim.format(listing_id=listing.id),
        headers=bearer_for(claimant),
    )
    assert first.status_code == status.HTTP_200_OK

    second = db_client.post(
        reuse_paths.claim.format(listing_id=listing.id),
        headers=bearer_for(claimant),
    )
    assert second.status_code == status.HTTP_409_CONFLICT


# ---------------------------------------------------------------------------
# REU-C04 | Cannot claim rejected listing
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_cannot_claim_rejected_listing(
    db_client, reuse_paths, donor, claimant, bearer_for, make_listing, test_zone
):
    """REU-C04 | Claiming REJECTED listing → 409."""
    listing = make_listing(
        donor=donor,
        zone=test_zone,
        status=ReuseStatus.REJECTED,
        rejection_reason="Already distributed",
    )
    response = db_client.post(
        reuse_paths.claim.format(listing_id=listing.id),
        headers=bearer_for(claimant),
    )
    assert response.status_code == status.HTTP_409_CONFLICT


# ---------------------------------------------------------------------------
# REU-C05 | Cannot claim pending-approval listing
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_cannot_claim_pending_listing(
    db_client, reuse_paths, donor, claimant, bearer_for, make_listing, test_zone
):
    """REU-C05 | Claiming PENDING_APPROVAL listing → 409."""
    listing = make_listing(
        donor=donor,
        zone=test_zone,
        status=ReuseStatus.PENDING_APPROVAL,
    )
    response = db_client.post(
        reuse_paths.claim.format(listing_id=listing.id),
        headers=bearer_for(claimant),
    )
    assert response.status_code == status.HTTP_409_CONFLICT


# ---------------------------------------------------------------------------
# REU-C06 | Cannot claim completed listing
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_cannot_claim_completed_listing(
    db_client, reuse_paths, donor, claimant, bearer_for, make_listing, test_zone
):
    """REU-C06 | Claiming COMPLETED listing → 409."""
    listing = make_listing(
        donor=donor,
        zone=test_zone,
        status=ReuseStatus.COMPLETED,
    )
    response = db_client.post(
        reuse_paths.claim.format(listing_id=listing.id),
        headers=bearer_for(claimant),
    )
    assert response.status_code == status.HTTP_409_CONFLICT


# ---------------------------------------------------------------------------
# REU-C07 | Claim nonexistent listing → 404
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_claim_nonexistent_listing_returns_404(db_client, reuse_paths, claimant, bearer_for):
    """REU-C07 | Claiming nonexistent listing → 404."""
    response = db_client.post(
        reuse_paths.claim.format(listing_id=uuid.uuid4()),
        headers=bearer_for(claimant),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# REU-C08 | My claims with status filter
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_my_claims_filter_by_status(
    db_client,
    reuse_paths,
    donor,
    claimant,
    bearer_for,
    make_listing,
    make_claim,
    test_zone,
):
    """REU-C08 | Filtering my_claims by COMPLETED returns approved claims."""
    listing = make_listing(donor=donor, zone=test_zone, status=ReuseStatus.COMPLETED)
    claim = make_claim(
        listing=listing,
        claimant=claimant,
        status=ReuseClaimStatus.APPROVED,
    )
    response = db_client.get(
        reuse_paths.my_claims,
        params={"filter": "COMPLETED"},
        headers=bearer_for(claimant),
    )
    assert response.status_code == status.HTTP_200_OK
    assert [item["id"] for item in response.json()] == [str(claim.id)]


@pytest.mark.api
def test_my_claims_filter_claim_requested(
    db_client,
    reuse_paths,
    donor,
    claimant,
    bearer_for,
    make_listing,
    make_claim,
    test_zone,
):
    """REU-C08b | CLAIM_REQUESTED filter returns pending claims."""
    listing = make_listing(donor=donor, zone=test_zone, status=ReuseStatus.CLAIM_PENDING)
    claim = make_claim(
        listing=listing,
        claimant=claimant,
        status=ReuseClaimStatus.PENDING,
    )
    response = db_client.get(
        reuse_paths.my_claims,
        params={"filter": "CLAIM_REQUESTED"},
        headers=bearer_for(claimant),
    )
    assert response.status_code == status.HTTP_200_OK
    ids = [item["id"] for item in response.json()]
    assert str(claim.id) in ids


# ---------------------------------------------------------------------------
# REU-C09 | My claims — cross-user isolation
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.security
def test_my_claims_cross_user_isolation(
    db_client,
    reuse_paths,
    donor,
    claimant,
    second_claimant,
    bearer_for,
    make_listing,
    make_claim,
    test_zone,
):
    """REU-C09 | Claimant A cannot see claimant B's claims."""
    listing = make_listing(donor=donor, zone=test_zone, status=ReuseStatus.CLAIM_PENDING)
    make_claim(listing=listing, claimant=claimant)

    response = db_client.get(reuse_paths.my_claims, headers=bearer_for(second_claimant))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []
