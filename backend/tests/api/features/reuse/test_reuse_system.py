"""Full system journey test for SCRUM-178 Reuse QA.

End-to-end flow: donation creation → manager approval → claim →
claim approval → listing completed, with notification verification
at each step and final contact-info exchange validation.
"""

from __future__ import annotations

import pytest
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.notifications.models import Notification


@pytest.mark.api
def test_reuse_system_journey(
    db_client,
    reuse_paths,
    manager,
    donor,
    claimant,
    second_claimant,
    bearer_for,
    db: Session,
):
    """REU-SYS | System journey: donate → approve → claim → approve claim.

    Steps:
    1. Donor creates a donation
    2. Manager approves the donation
    3. Claimant claims the item
    4. Second claimant also claims the item (should fail — CLAIM_PENDING)
    5. Manager approves claimant A's claim
    6. Verify listing COMPLETED, claim A approved, claimant notified
    7. Verify claimant sees donor contact info in approved claim
    8. Verify donor sees listing as COMPLETED in my_donations
    """
    headers_donor = bearer_for(donor)
    headers_claimant = bearer_for(claimant)
    headers_mgr = bearer_for(manager)

    # ------- Step 1: Donor creates donation -------
    create_resp = db_client.post(
        reuse_paths.donations,
        headers=headers_donor,
        json={
            "title": "Journey Desk",
            "category": "FURNITURE",
            "description": "Solid wood desk",
            "condition": "GOOD",
            "address": "100 Green Lane",
            "images": ["desk1.jpg", "desk2.jpg"],
        },
    )
    assert create_resp.status_code == status.HTTP_200_OK, f"Step 1 failed: {create_resp.text}"
    listing_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "PENDING_APPROVAL"
    assert create_resp.json()["address"] == "100 Green Lane"
    assert create_resp.json()["images"] == ["desk1.jpg", "desk2.jpg"]

    # Verify donor notification
    donor_notif = db.scalar(
        select(Notification).where(
            Notification.user_id == donor.id,
            Notification.title == "Donation submitted",
        )
    )
    assert donor_notif is not None, "Step 1: Donor should receive submission notification"

    # ------- Step 2: Manager approves donation -------
    approve_resp = db_client.post(
        reuse_paths.review_donation.format(listing_id=listing_id),
        headers=headers_mgr,
        json={"status": "AVAILABLE"},
    )
    assert approve_resp.status_code == status.HTTP_200_OK, f"Step 2 failed: {approve_resp.text}"
    assert approve_resp.json()["status"] == "AVAILABLE"

    # Verify donor approval notification
    approve_notif = db.scalar(
        select(Notification).where(
            Notification.user_id == donor.id,
            Notification.title == "Donation approved",
        )
    )
    assert approve_notif is not None, "Step 2: Donor should receive approval notification"

    # ------- Step 3: Item visible on shelf -------
    shelf_resp = db_client.get(reuse_paths.shelf, headers=headers_claimant)
    assert shelf_resp.status_code == status.HTTP_200_OK
    shelf_ids = {item["id"] for item in shelf_resp.json()}
    assert listing_id in shelf_ids, "Step 3: Approved listing should appear on shelf"

    # ------- Step 4: Claimant claims the item -------
    claim_resp = db_client.post(
        reuse_paths.claim.format(listing_id=listing_id),
        headers=headers_claimant,
    )
    assert claim_resp.status_code == status.HTTP_200_OK, f"Step 4 failed: {claim_resp.text}"
    assert claim_resp.json()["status"] == "CLAIM_REQUESTED"

    # ------- Step 5: Second claimant tries to claim (CLAIM_PENDING → 409) -------
    second_claim_resp = db_client.post(
        reuse_paths.claim.format(listing_id=listing_id),
        headers=bearer_for(second_claimant),
    )
    assert second_claim_resp.status_code == status.HTTP_409_CONFLICT, (
        f"Step 5: Second claim should be rejected, got {second_claim_resp.status_code}"
    )

    # ------- Step 6: Manager sees pending claims -------
    pending_resp = db_client.get(reuse_paths.pending_claims, headers=headers_mgr)
    assert pending_resp.status_code == status.HTTP_200_OK
    pending_claims = pending_resp.json()
    matching = [c for c in pending_claims if c["listing_id"] == listing_id]
    assert len(matching) >= 1, "Step 6: Manager should see pending claim"
    claim_id = matching[0]["id"]

    # ------- Step 7: Manager approves the claim -------
    claim_approve = db_client.post(
        reuse_paths.review_claim.format(claim_id=claim_id),
        headers=headers_mgr,
        json={"status": "APPROVED", "note": "Good to go!"},
    )
    assert claim_approve.status_code == status.HTTP_200_OK, f"Step 7 failed: {claim_approve.text}"

    # Verify claimant notification
    claim_notif = db.scalar(
        select(Notification).where(
            Notification.user_id == claimant.id,
            Notification.title == "Claim request approved",
        )
    )
    assert claim_notif is not None, "Step 7: Claimant should receive approval notification"

    # Verify donor notification
    donor_claimed = db.scalar(
        select(Notification).where(
            Notification.user_id == donor.id,
            Notification.title == "Donation claimed",
        )
    )
    assert donor_claimed is not None, "Step 7: Donor should be notified of claim"

    # ------- Step 8: Claimant sees donor contact info -------
    my_claims = db_client.get(
        reuse_paths.my_claims,
        params={"filter": "COMPLETED"},
        headers=headers_claimant,
    )
    assert my_claims.status_code == status.HTTP_200_OK
    completed = my_claims.json()
    assert len(completed) >= 1
    approved_claim = completed[0]
    assert approved_claim["donor_phone"] is not None, (
        "Step 8: Approved claim should reveal donor phone"
    )
    assert approved_claim["donor_email"] is not None, (
        "Step 8: Approved claim should reveal donor email"
    )

    # ------- Step 9: Donor sees COMPLETED listing -------
    my_donations = db_client.get(reuse_paths.my_donations, headers=headers_donor)
    assert my_donations.status_code == status.HTTP_200_OK
    my_listings = my_donations.json()
    journey_listing = [d for d in my_listings if d["id"] == listing_id]
    assert len(journey_listing) == 1
    assert journey_listing[0]["status"] == "COMPLETED"

    # ------- Step 10: Completed listing no longer on shelf -------
    shelf_after = db_client.get(reuse_paths.shelf, headers=headers_claimant)
    shelf_after_ids = {item["id"] for item in shelf_after.json()}
    assert listing_id not in shelf_after_ids, (
        "Step 10: Completed listing should not appear on shelf"
    )
