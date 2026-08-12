import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.features.manager.dependencies import require_manager
from app.features.reuse.models import ReuseClaim, ReuseListing
from app.features.reuse.schemas import (
    ClaimResponse,
    ClaimReview,
    DonationCreate,
    DonationResponse,
    DonationReview,
)
from app.features.reuse.service import (
    claim_donation,
    create_donation,
    list_manager_all_donations,
    list_manager_pending_claims,
    list_manager_pending_donations,
    list_my_claims,
    list_my_donations,
    list_shelf_items,
    review_claim,
    review_donation,
)
from app.features.users.dependencies import require_citizen
from app.features.users.models import User
from app.models.enums import ReuseClaimStatus, ReuseStatus

router = APIRouter(prefix="/reuse", tags=["Civic Reuse Exchange"])


def format_donation_response(listing: ReuseListing) -> DonationResponse:
    import re

    claimant_id = None
    claimant_name = None
    claimant_phone = None
    claimant_email = None

    # Retrieve active claim details (PENDING or APPROVED)
    if listing.claims:
        for claim in listing.claims:
            if claim.status in [ReuseClaimStatus.PENDING, ReuseClaimStatus.APPROVED]:
                claimant_id = claim.claimant_id
                if claim.claimant:
                    claimant_name = claim.claimant.name
                    claimant_phone = claim.claimant.phone
                    claimant_email = claim.claimant.email
                break

    # Translate CLAIM_PENDING in DB to CLAIM_REQUESTED for frontend compatibility
    status_str = listing.status.value
    if listing.status == ReuseStatus.CLAIM_PENDING:
        status_str = "CLAIM_REQUESTED"

    # Extract inline address if stored in description
    addr = None
    desc = listing.description
    if desc:
        match = re.search(r"\n\n\[Pickup Location: (.*?)\]$", desc)
        if match:
            addr = match.group(1)
            desc = desc[: match.start()]

    return DonationResponse(
        id=listing.id,
        donor_id=listing.lister_id,
        donor_name=listing.lister.name if listing.lister else "Unknown",
        donor_phone=listing.lister.phone if listing.lister else None,
        donor_email=listing.lister.email if listing.lister else None,
        title=listing.title,
        category=listing.category.value,
        description=desc,
        condition=listing.condition.value,
        status=status_str,
        address=addr,
        images=[img.img_url for img in sorted(listing.images, key=lambda x: x.sort_order)],
        rejection_reason=listing.rejection_reason,
        manager_notes=listing.manager_notes,
        claimant_id=claimant_id,
        claimant_name=claimant_name,
        claimant_phone=claimant_phone,
        claimant_email=claimant_email,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
    )


def format_claim_response(claim: ReuseClaim) -> ClaimResponse:
    import re

    addr = None
    desc = None
    category = None
    condition = None
    images = []
    donor_name = None
    donor_phone = None
    donor_email = None

    if claim.listing:
        desc = claim.listing.description
        if desc:
            match = re.search(r"\n\n\[Pickup Location: (.*?)\]$", desc)
            if match:
                addr = match.group(1)
                desc = desc[: match.start()]
        category = claim.listing.category.value
        condition = claim.listing.condition.value
        images = [img.img_url for img in sorted(claim.listing.images, key=lambda x: x.sort_order)]
        if claim.listing.lister:
            donor_name = claim.listing.lister.name
            if claim.status == ReuseClaimStatus.APPROVED:
                donor_phone = claim.listing.lister.phone
                donor_email = claim.listing.lister.email

    return ClaimResponse(
        id=claim.id,
        listing_id=claim.listing_id,
        title=claim.listing.title if claim.listing else "Unknown",
        description=desc,
        category=category,
        condition=condition,
        images=images,
        address=addr,
        claimant_id=claim.claimant_id,
        claimant_name=claim.claimant.name if claim.claimant else "Unknown",
        status=claim.status.value,
        note=claim.note,
        donor_name=donor_name,
        donor_phone=donor_phone,
        donor_email=donor_email,
        decided_at=claim.decided_at,
        created_at=claim.created_at,
        updated_at=claim.decided_at or claim.created_at,
    )


# ── Citizen / User endpoints ──


@router.post("/donations", response_model=DonationResponse)
def citizen_create_donation(
    payload: DonationCreate,
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
) -> Any:
    """Create a new donation listing as a citizen."""
    listing = create_donation(db, current_user, payload)
    # Reload with relationships
    listing = db.scalar(
        select(ReuseListing)
        .where(ReuseListing.id == listing.id)
        .options(
            joinedload(ReuseListing.lister),
            joinedload(ReuseListing.images),
            joinedload(ReuseListing.claims).joinedload(ReuseClaim.claimant),
        )
    )
    return format_donation_response(listing)


@router.get("/donations/my", response_model=list[DonationResponse])
def citizen_list_my_donations(
    current_user: User = Depends(require_citizen), db: Session = Depends(get_db)
) -> Any:
    """List all donation listings submitted by the current citizen."""
    listings = list_my_donations(db, current_user.id)
    return [format_donation_response(item) for item in listings]


@router.get("/claims/my", response_model=list[ClaimResponse])
def citizen_list_my_claims(
    filter: str = "", current_user: User = Depends(require_citizen), db: Session = Depends(get_db)
) -> Any:
    """List all items claimed by the current citizen."""
    claims = list_my_claims(db, current_user.id, filter)
    return [format_claim_response(c) for c in claims]


@router.get("/shelf", response_model=list[DonationResponse])
def get_public_shelf(
    search: str = "",
    category: str = "",
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
) -> Any:
    """Get all live, available donation listings on the Community Shelf (excluding own)."""
    listings = list_shelf_items(db, current_user.id, search, category)
    return [format_donation_response(item) for item in listings]


@router.post("/donations/{listing_id}/claim", response_model=DonationResponse)
def citizen_claim_item(
    listing_id: uuid.UUID,
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
) -> Any:
    """Claim an available item from the Community Shelf."""
    listing = claim_donation(db, current_user, listing_id)
    # Reload with relationships
    listing = db.scalar(
        select(ReuseListing)
        .where(ReuseListing.id == listing.id)
        .options(
            joinedload(ReuseListing.lister),
            joinedload(ReuseListing.images),
            joinedload(ReuseListing.claims).joinedload(ReuseClaim.claimant),
        )
    )
    return format_donation_response(listing)


@router.post("/donations/{listing_id}/withdraw", response_model=DonationResponse)
def citizen_withdraw_item(
    listing_id: uuid.UUID,
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
) -> Any:
    """Withdraw a pending donation listing."""
    listing = db.scalar(
        select(ReuseListing)
        .where(ReuseListing.id == listing_id)
        .options(
            joinedload(ReuseListing.lister),
            joinedload(ReuseListing.images),
            joinedload(ReuseListing.claims).joinedload(ReuseClaim.claimant),
        )
    )
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Donation listing not found."
        )
    if listing.lister_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You can only withdraw your own listing."
        )
    if listing.status != ReuseStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only a listing still pending approval can be withdrawn.",
        )

    listing.status = ReuseStatus.WITHDRAWN
    db.commit()
    db.refresh(listing)
    return format_donation_response(listing)


# ── Manager review endpoints ──


@router.get("/manager/donations/pending", response_model=list[DonationResponse])
def manager_get_pending_donations(
    current_user: User = Depends(require_manager), db: Session = Depends(get_db)
) -> Any:
    """Get all pending donation listings in manager's supervised wards."""
    listings = list_manager_pending_donations(db, current_user)
    return [format_donation_response(item) for item in listings]


@router.get("/manager/donations", response_model=list[DonationResponse])
def manager_get_all_donations(
    current_user: User = Depends(require_manager), db: Session = Depends(get_db)
) -> Any:
    """Get all donation listings in manager's supervised wards."""
    listings = list_manager_all_donations(db, current_user)
    return [format_donation_response(item) for item in listings]


@router.get("/manager/claims/pending", response_model=list[ClaimResponse])
def manager_get_pending_claims(
    current_user: User = Depends(require_manager), db: Session = Depends(get_db)
) -> Any:
    """Get all pending claim requests in manager's supervised wards."""
    claims = list_manager_pending_claims(db, current_user)
    return [format_claim_response(c) for c in claims]


@router.post("/donations/{listing_id}/review", response_model=DonationResponse)
def manager_review_item(
    listing_id: uuid.UUID,
    payload: DonationReview,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> Any:
    """Approve or reject a donation listing."""
    listing = review_donation(db, current_user, listing_id, payload)
    # Reload with relationships
    listing = db.scalar(
        select(ReuseListing)
        .where(ReuseListing.id == listing.id)
        .options(
            joinedload(ReuseListing.lister),
            joinedload(ReuseListing.images),
            joinedload(ReuseListing.claims).joinedload(ReuseClaim.claimant),
        )
    )
    return format_donation_response(listing)


@router.post("/claims/{claim_id}/review", response_model=ClaimResponse)
def manager_review_claim_request(
    claim_id: uuid.UUID,
    payload: ClaimReview,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> Any:
    """Approve or reject a claim request."""
    claim = review_claim(db, current_user, claim_id, payload)
    # Reload with relationships
    claim = db.scalar(
        select(ReuseClaim)
        .where(ReuseClaim.id == claim.id)
        .options(
            joinedload(ReuseClaim.listing).joinedload(ReuseListing.lister),
            joinedload(ReuseClaim.claimant),
        )
    )
    return format_claim_response(claim)
