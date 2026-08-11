"""Manager moderation tests for SCRUM-178 Reuse QA.

Covers: donation approval, donation rejection (with/without reason),
claim approval (with auto-reject), claim rejection (with/without note),
ward scoping, unassigned manager bypass, pending listing views,
nonexistent review targets, and notification delivery.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.notifications.models import Notification
from app.models.enums import ReuseClaimStatus, ReuseStatus, Role

# ---------------------------------------------------------------------------
# REU-M01 | Manager approves donation
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_manager_approves_donation(
    db_client,
    reuse_paths,
    manager,
    donor,
    bearer_for,
    make_listing,
    test_zone,
    db: Session,
):
    """REU-M01 | Approve donation → AVAILABLE, donor notified."""
    listing = make_listing(donor=donor, zone=test_zone)
    response = db_client.post(
        reuse_paths.review_donation.format(listing_id=listing.id),
        headers=bearer_for(manager),
        json={"status": "AVAILABLE"},
    )
    assert response.status_code == status.HTTP_200_OK
    db.refresh(listing)
    assert listing.status == ReuseStatus.AVAILABLE
    assert listing.reviewed_by_id == manager.id

    # Donor notification
    notifs = db.scalars(
        select(Notification).where(
            Notification.user_id == donor.id,
            Notification.title == "Donation approved",
        )
    ).all()
    assert len(notifs) >= 1


# ---------------------------------------------------------------------------
# REU-M02 | Manager rejects donation with valid reason
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_manager_rejects_donation_with_reason(
    db_client,
    reuse_paths,
    manager,
    donor,
    bearer_for,
    make_listing,
    test_zone,
    db: Session,
):
    """REU-M02 | Reject donation with reason → REJECTED, donor notified."""
    listing = make_listing(donor=donor, zone=test_zone)
    response = db_client.post(
        reuse_paths.review_donation.format(listing_id=listing.id),
        headers=bearer_for(manager),
        json={"status": "REJECTED", "rejection_reason": "Inappropriate item"},
    )
    assert response.status_code == status.HTTP_200_OK
    db.refresh(listing)
    assert listing.status == ReuseStatus.REJECTED
    assert listing.rejection_reason == "Inappropriate item"

    notifs = db.scalars(
        select(Notification).where(
            Notification.user_id == donor.id,
            Notification.title == "Donation rejected",
        )
    ).all()
    assert len(notifs) >= 1


# ---------------------------------------------------------------------------
# REU-M03 | Manager rejects donation without reason → 422
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.boundary
def test_manager_rejects_donation_without_reason(
    db_client,
    reuse_paths,
    manager,
    donor,
    bearer_for,
    make_listing,
    test_zone,
    db: Session,
):
    """REU-M03 | Reject without reason → 422, listing unchanged."""
    listing = make_listing(donor=donor, zone=test_zone)
    response = db_client.post(
        reuse_paths.review_donation.format(listing_id=listing.id),
        headers=bearer_for(manager),
        json={"status": "REJECTED", "rejection_reason": "   "},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    db.refresh(listing)
    assert listing.status == ReuseStatus.PENDING_APPROVAL


# ---------------------------------------------------------------------------
# REU-M04 | Manager without ward cannot review donation
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.security
def test_manager_without_ward_cannot_review_donation(
    db_client,
    reuse_paths,
    make_user,
    donor,
    bearer_for,
    make_listing,
    test_zone,
):
    """REU-M04 | Unassigned manager reviewing donation → 403.

    KNOWN DEFECT: get_managed_zone_ids returns [] for unassigned managers,
    and review_donation only enforces ward boundaries when the list is
    non-empty. This test currently FAILS with 200 instead of 403.
    """
    unassigned_manager = make_user(role=Role.MUNICIPAL_OFFICER)
    listing = make_listing(donor=donor, zone=test_zone)
    response = db_client.post(
        reuse_paths.review_donation.format(listing_id=listing.id),
        headers=bearer_for(unassigned_manager),
        json={"status": "AVAILABLE"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# REU-M05 | Manager cannot review donation outside their ward
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.security
def test_manager_cannot_review_donation_outside_ward(
    db_client,
    reuse_paths,
    manager,
    donor,
    make_user,
    second_zone,
    bearer_for,
    make_listing,
    db: Session,
):
    """REU-M05 | Manager from ward A cannot review donation in ward B."""
    # Create a donor in second zone
    other_donor = make_user(zone=second_zone)
    listing = make_listing(donor=other_donor, zone=second_zone)
    response = db_client.post(
        reuse_paths.review_donation.format(listing_id=listing.id),
        headers=bearer_for(manager),
        json={"status": "AVAILABLE"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------------------------------------------------------------------------
# REU-M06 | Review nonexistent donation → 404
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_review_nonexistent_donation_returns_404(db_client, reuse_paths, manager, bearer_for):
    """REU-M06 | Reviewing nonexistent donation → 404."""
    response = db_client.post(
        reuse_paths.review_donation.format(listing_id=uuid.uuid4()),
        headers=bearer_for(manager),
        json={"status": "AVAILABLE"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# REU-M07 | Invalid review status → 422
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.boundary
def test_invalid_donation_review_status(
    db_client, reuse_paths, manager, donor, bearer_for, make_listing, test_zone
):
    """REU-M07 | Invalid review status string → 422."""
    listing = make_listing(donor=donor, zone=test_zone)
    response = db_client.post(
        reuse_paths.review_donation.format(listing_id=listing.id),
        headers=bearer_for(manager),
        json={"status": "NONSENSE"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ---------------------------------------------------------------------------
# REU-M08 | Manager approves claim → COMPLETED, other claims rejected
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_manager_approves_claim_completes_listing(
    db_client,
    reuse_paths,
    manager,
    donor,
    claimant,
    bearer_for,
    make_listing,
    make_claim,
    test_zone,
    db: Session,
):
    """REU-M08 | Approve claim → listing COMPLETED, claimant notified."""
    listing = make_listing(donor=donor, zone=test_zone, status=ReuseStatus.CLAIM_PENDING)
    claim = make_claim(listing=listing, claimant=claimant)
    response = db_client.post(
        reuse_paths.review_claim.format(claim_id=claim.id),
        headers=bearer_for(manager),
        json={"status": "APPROVED", "note": "Approved for exchange."},
    )
    assert response.status_code == status.HTTP_200_OK
    db.refresh(listing)
    db.refresh(claim)
    assert listing.status == ReuseStatus.COMPLETED
    assert claim.status == ReuseClaimStatus.APPROVED
    assert claim.decided_by_id == manager.id
    assert claim.note == "Approved for exchange."

    # Claimant notification
    notifs = db.scalars(
        select(Notification).where(
            Notification.user_id == claimant.id,
            Notification.title == "Claim request approved",
        )
    ).all()
    assert len(notifs) >= 1

    # Donor notification
    donor_notifs = db.scalars(
        select(Notification).where(
            Notification.user_id == donor.id,
            Notification.title == "Donation claimed",
        )
    ).all()
    assert len(donor_notifs) >= 1


# ---------------------------------------------------------------------------
# REU-M09 | Approving one claim auto-rejects others
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_approving_one_claim_rejects_other_pending_claims(
    db_client,
    reuse_paths,
    manager,
    donor,
    claimant,
    second_claimant,
    bearer_for,
    make_listing,
    make_claim,
    test_zone,
    db: Session,
):
    """REU-M09 | Approving claim A auto-rejects claim B."""
    listing = make_listing(donor=donor, zone=test_zone, status=ReuseStatus.CLAIM_PENDING)
    selected = make_claim(listing=listing, claimant=claimant)
    other = make_claim(listing=listing, claimant=second_claimant)

    response = db_client.post(
        reuse_paths.review_claim.format(claim_id=selected.id),
        headers=bearer_for(manager),
        json={"status": "APPROVED"},
    )
    assert response.status_code == status.HTTP_200_OK
    db.refresh(selected)
    db.refresh(other)
    assert selected.status == ReuseClaimStatus.APPROVED
    assert other.status == ReuseClaimStatus.REJECTED
    assert other.note == "Another claim was approved."


# ---------------------------------------------------------------------------
# REU-M10 | Manager rejects claim with note → listing reopens
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_manager_rejects_claim_and_reopens_listing(
    db_client,
    reuse_paths,
    manager,
    donor,
    claimant,
    bearer_for,
    make_listing,
    make_claim,
    test_zone,
    db: Session,
):
    """REU-M10 | Reject claim → listing back to AVAILABLE, claimant notified."""
    listing = make_listing(donor=donor, zone=test_zone, status=ReuseStatus.CLAIM_PENDING)
    claim = make_claim(listing=listing, claimant=claimant)
    response = db_client.post(
        reuse_paths.review_claim.format(claim_id=claim.id),
        headers=bearer_for(manager),
        json={"status": "REJECTED", "note": "Pickup arrangement failed."},
    )
    assert response.status_code == status.HTTP_200_OK
    db.refresh(listing)
    db.refresh(claim)
    assert listing.status == ReuseStatus.AVAILABLE
    assert claim.status == ReuseClaimStatus.REJECTED
    assert claim.note == "Pickup arrangement failed."

    # Claimant notification
    notifs = db.scalars(
        select(Notification).where(
            Notification.user_id == claimant.id,
            Notification.title == "Claim request rejected",
        )
    ).all()
    assert len(notifs) >= 1


# ---------------------------------------------------------------------------
# REU-M11 | Manager rejects claim without note → 422
# ---------------------------------------------------------------------------


@pytest.mark.api
@pytest.mark.boundary
def test_manager_rejects_claim_without_note(
    db_client,
    reuse_paths,
    manager,
    donor,
    claimant,
    bearer_for,
    make_listing,
    make_claim,
    test_zone,
    db: Session,
):
    """REU-M11 | Reject claim with whitespace-only note → 422."""
    listing = make_listing(donor=donor, zone=test_zone, status=ReuseStatus.CLAIM_PENDING)
    claim = make_claim(listing=listing, claimant=claimant)
    response = db_client.post(
        reuse_paths.review_claim.format(claim_id=claim.id),
        headers=bearer_for(manager),
        json={"status": "REJECTED", "note": " "},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    db.refresh(claim)
    assert claim.status == ReuseClaimStatus.PENDING


# ---------------------------------------------------------------------------
# REU-M12 | Review nonexistent claim → 404
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_review_nonexistent_claim_returns_404(db_client, reuse_paths, manager, bearer_for):
    """REU-M12 | Reviewing nonexistent claim → 404."""
    response = db_client.post(
        reuse_paths.review_claim.format(claim_id=uuid.uuid4()),
        headers=bearer_for(manager),
        json={"status": "APPROVED"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


# ---------------------------------------------------------------------------
# REU-M13 | Manager pending donations list
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_manager_lists_pending_donations(
    db_client,
    reuse_paths,
    manager,
    donor,
    bearer_for,
    make_listing,
    test_zone,
):
    """REU-M13 | Manager sees pending donations in their zone."""
    pending = make_listing(donor=donor, zone=test_zone, status=ReuseStatus.PENDING_APPROVAL)
    make_listing(donor=donor, zone=test_zone, status=ReuseStatus.AVAILABLE)

    response = db_client.get(reuse_paths.pending_donations, headers=bearer_for(manager))
    assert response.status_code == status.HTTP_200_OK
    ids = {item["id"] for item in response.json()}
    assert str(pending.id) in ids


# ---------------------------------------------------------------------------
# REU-M14 | Manager all donations list
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_manager_lists_all_donations(
    db_client,
    reuse_paths,
    manager,
    donor,
    bearer_for,
    make_listing,
    test_zone,
):
    """REU-M14 | Manager sees all donations (any status) in their zone."""
    pending = make_listing(donor=donor, zone=test_zone, status=ReuseStatus.PENDING_APPROVAL)
    available = make_listing(donor=donor, zone=test_zone, status=ReuseStatus.AVAILABLE)

    response = db_client.get(reuse_paths.all_donations, headers=bearer_for(manager))
    assert response.status_code == status.HTTP_200_OK
    ids = {item["id"] for item in response.json()}
    assert str(pending.id) in ids
    assert str(available.id) in ids


# ---------------------------------------------------------------------------
# REU-M15 | Manager pending claims list
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_manager_lists_pending_claims(
    db_client,
    reuse_paths,
    manager,
    donor,
    claimant,
    bearer_for,
    make_listing,
    make_claim,
    test_zone,
):
    """REU-M15 | Manager sees pending claims in their zone."""
    listing = make_listing(donor=donor, zone=test_zone, status=ReuseStatus.CLAIM_PENDING)
    claim = make_claim(listing=listing, claimant=claimant)

    response = db_client.get(reuse_paths.pending_claims, headers=bearer_for(manager))
    assert response.status_code == status.HTTP_200_OK
    ids = {item["id"] for item in response.json()}
    assert str(claim.id) in ids


# ---------------------------------------------------------------------------
# REU-M16 | Approved claim reveals donor contact info
# ---------------------------------------------------------------------------


@pytest.mark.api
def test_approved_claim_reveals_donor_contact(
    db_client,
    reuse_paths,
    manager,
    donor,
    claimant,
    bearer_for,
    make_listing,
    make_claim,
    test_zone,
):
    """REU-M16 | After claim approval, claimant sees donor phone/email."""
    listing = make_listing(donor=donor, zone=test_zone, status=ReuseStatus.CLAIM_PENDING)
    claim = make_claim(listing=listing, claimant=claimant)

    # Approve
    db_client.post(
        reuse_paths.review_claim.format(claim_id=claim.id),
        headers=bearer_for(manager),
        json={"status": "APPROVED"},
    )

    # Check my_claims reveals donor contact
    response = db_client.get(
        reuse_paths.my_claims,
        params={"filter": "COMPLETED"},
        headers=bearer_for(claimant),
    )
    assert response.status_code == status.HTTP_200_OK
    claims = response.json()
    assert len(claims) >= 1
    approved = claims[0]
    assert approved["donor_phone"] is not None
    assert approved["donor_email"] is not None
