"""Donation listing tests for SCRUM-178 Reuse QA.

Covers: creation, persistence, address/image handling, withdrawal lifecycle,
title validation (adversarial), notifications, and cross-user isolation.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.notifications.models import Notification
from app.features.reuse.models import ReuseListing
from app.models.enums import ReuseStatus

BASE_PAYLOAD = {
    "title": "Desk Lamp",
    "category": "FURNITURE",
    "description": "Solid desk lamp, works perfectly.",
    "condition": "GOOD",
}


# ---------------------------------------------------------------------------
# REU-D01 | Create donation — happy path
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_create_donation_persists_pending_listing(
    db_client, reuse_paths, donor, manager, bearer_for, db: Session
):
    """REU-D01 | Create donation → PENDING_APPROVAL, notifications sent."""
    response = db_client.post(
        reuse_paths.donations,
        headers=bearer_for(donor),
        json={
            **BASE_PAYLOAD,
            "address": "42 Green Street",
            "images": ["z.jpg", "a.jpg"],
        },
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "PENDING_APPROVAL"
    assert body["address"] == "42 Green Street"
    assert body["images"] == ["z.jpg", "a.jpg"]
    assert body["donor_id"] == str(donor.id)
    assert body["title"] == "Desk Lamp"

    # DB persistence
    listing = db.get(ReuseListing, body["id"])
    assert listing is not None
    assert listing.status == ReuseStatus.PENDING_APPROVAL

    # Donor notification
    donor_notifs = db.scalars(select(Notification).where(Notification.user_id == donor.id)).all()
    assert any(n.title == "Donation submitted" for n in donor_notifs)

    # Manager notification
    mgr_notifs = db.scalars(select(Notification).where(Notification.user_id == manager.id)).all()
    assert any(n.title == "New donation pending review" for n in mgr_notifs)


# ---------------------------------------------------------------------------
# REU-D02 | Create donation — minimal payload (no optional fields)
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_create_donation_minimal_payload(db_client, reuse_paths, donor, manager, bearer_for):
    """REU-D02 | Minimal payload (no description, address, images) succeeds."""
    response = db_client.post(
        reuse_paths.donations,
        headers=bearer_for(donor),
        json={"title": "Old Book", "category": "BOOKS", "condition": "FAIR"},
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "PENDING_APPROVAL"
    assert body["images"] == []
    assert body["address"] is None


# ---------------------------------------------------------------------------
# REU-D03 | Create donation — category mapping
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.parametrize(
    "input_cat, expected_db_cat",
    [
        ("FURNITURE", "FURNITURE"),
        ("BOOKS", "BOOKS"),
        ("ELECTRONICS", "ELECTRONICS"),
        ("CLOTHING", "CLOTHING"),
        ("CLOTHES", "CLOTHING"),
        ("TOYS", "HOUSEHOLD"),
        ("KITCHEN", "HOUSEHOLD"),
        ("RANDOM_JUNK", "OTHER"),
    ],
    ids=[
        "furniture",
        "books",
        "electronics",
        "clothing",
        "clothes-alias",
        "toys→household",
        "kitchen→household",
        "unknown→other",
    ],
)
def test_donation_category_mapping(
    db_client, reuse_paths, donor, manager, bearer_for, input_cat, expected_db_cat
):
    """REU-D03 | Frontend categories are correctly mapped to DB enums."""
    response = db_client.post(
        reuse_paths.donations,
        headers=bearer_for(donor),
        json={"title": f"Item-{input_cat}", "category": input_cat, "condition": "GOOD"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["category"] == expected_db_cat


# ---------------------------------------------------------------------------
# REU-D04 | Empty title
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.boundary
def test_empty_title_is_rejected(db_client, reuse_paths, donor, bearer_for):
    """REU-D04 | Empty donation title → 422.

    KNOWN DEFECT: DonationCreate has max_length=80 but no min_length or
    non-empty validator. The service accepts and stores "".
    """
    response = db_client.post(
        reuse_paths.donations,
        headers=bearer_for(donor),
        json={**BASE_PAYLOAD, "title": ""},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ---------------------------------------------------------------------------
# REU-D05 | Whitespace-only title
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.boundary
def test_whitespace_only_title_is_rejected(db_client, reuse_paths, donor, bearer_for):
    """REU-D05 | Whitespace-only title → 422.

    KNOWN DEFECT: title.strip() produces empty string but is accepted.
    """
    response = db_client.post(
        reuse_paths.donations,
        headers=bearer_for(donor),
        json={**BASE_PAYLOAD, "title": "   "},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ---------------------------------------------------------------------------
# REU-D06 | Max-length title
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.boundary
def test_overlength_title_is_rejected(db_client, reuse_paths, donor, bearer_for):
    """REU-D06 | Title exceeding 80 chars → 422."""
    response = db_client.post(
        reuse_paths.donations,
        headers=bearer_for(donor),
        json={**BASE_PAYLOAD, "title": "X" * 81},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.api
@pytest.mark.boundary
def test_max_length_title_is_accepted(db_client, reuse_paths, donor, manager, bearer_for):
    """REU-D06b | Title at exactly 80 chars succeeds."""
    response = db_client.post(
        reuse_paths.donations,
        headers=bearer_for(donor),
        json={**BASE_PAYLOAD, "title": "X" * 80},
    )
    assert response.status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# REU-D07 | Donor lists only own donations
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_donor_lists_only_own_donations(
    db_client, reuse_paths, donor, claimant, bearer_for, make_listing, test_zone
):
    """REU-D07 | my_donations returns only the current user's listings."""
    own = make_listing(donor=donor, zone=test_zone)
    make_listing(donor=claimant, zone=test_zone, title="Other person's item")

    response = db_client.get(reuse_paths.my_donations, headers=bearer_for(donor))
    assert response.status_code == status.HTTP_200_OK
    ids = [item["id"] for item in response.json()]
    assert str(own.id) in ids
    assert len(ids) == 1


# ---------------------------------------------------------------------------
# REU-D08 | Withdraw pending donation
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_pending_donation_can_be_withdrawn(
    db_client, reuse_paths, donor, bearer_for, make_listing, test_zone, db: Session
):
    """REU-D08 | Donor withdraws pending listing → WITHDRAWN."""
    listing = make_listing(donor=donor, zone=test_zone)
    response = db_client.post(
        reuse_paths.withdraw.format(listing_id=listing.id),
        headers=bearer_for(donor),
    )
    assert response.status_code == status.HTTP_200_OK
    db.refresh(listing)
    assert listing.status == ReuseStatus.WITHDRAWN


# ---------------------------------------------------------------------------
# REU-D09 | Cannot withdraw another donor's listing
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.security
def test_donor_cannot_withdraw_another_donors_listing(
    db_client, reuse_paths, donor, claimant, bearer_for, make_listing, test_zone
):
    """REU-D09 | Cross-user withdrawal blocked with 403."""
    listing = make_listing(donor=donor, zone=test_zone)
    response = db_client.post(
        reuse_paths.withdraw.format(listing_id=listing.id),
        headers=bearer_for(claimant),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# REU-D10 | Cannot withdraw approved/available donation
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_approved_donation_cannot_be_withdrawn(
    db_client, reuse_paths, donor, bearer_for, make_listing, test_zone
):
    """REU-D10 | Only PENDING_APPROVAL listings can be withdrawn."""
    listing = make_listing(donor=donor, zone=test_zone, status=ReuseStatus.AVAILABLE)
    response = db_client.post(
        reuse_paths.withdraw.format(listing_id=listing.id),
        headers=bearer_for(donor),
    )
    assert response.status_code == status.HTTP_409_CONFLICT


# ---------------------------------------------------------------------------
# REU-D11 | Withdraw nonexistent listing → 404
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_withdraw_nonexistent_listing_returns_404(db_client, reuse_paths, donor, bearer_for):
    """REU-D11 | Withdrawing nonexistent listing → 404."""
    response = db_client.post(
        reuse_paths.withdraw.format(listing_id=uuid.uuid4()),
        headers=bearer_for(donor),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
