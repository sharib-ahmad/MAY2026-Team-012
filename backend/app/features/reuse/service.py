import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.features.manager.service import get_managed_zone_ids, notify_zone_managers
from app.features.notifications.models import Notification
from app.features.reuse.models import ReuseClaim, ReuseImage, ReuseListing
from app.features.reuse.schemas import ClaimReview, DonationCreate, DonationReview
from app.features.users.models import User
from app.models.enums import ReuseCategory, ReuseClaimStatus, ReuseCondition, ReuseStatus, Role
from app.models.zone import Zone


def map_frontend_category(cat: str) -> ReuseCategory:
    cat_upper = cat.upper()
    if cat_upper in ["CLOTHES", "CLOTHING"]:
        return ReuseCategory.CLOTHING
    elif cat_upper == "BOOKS":
        return ReuseCategory.BOOKS
    elif cat_upper == "FURNITURE":
        return ReuseCategory.FURNITURE
    elif cat_upper == "ELECTRONICS":
        return ReuseCategory.ELECTRONICS
    elif cat_upper in ["TOYS", "KITCHEN", "HOUSEHOLD"]:
        return ReuseCategory.HOUSEHOLD
    else:
        return ReuseCategory.OTHER


def map_frontend_condition(cond: str) -> ReuseCondition:
    cond_upper = cond.upper()
    if cond_upper in ["NEW", "LIKE_NEW", "GOOD"]:
        return ReuseCondition.GOOD
    else:
        return ReuseCondition.FAIR


def get_donor_zone_id(db: Session, donor_id: uuid.UUID) -> uuid.UUID | None:
    return db.scalar(select(User.zone_id).where(User.id == donor_id))


def notify_user(db: Session, user_id: uuid.UUID, title: str, body: str) -> None:
    db.add(Notification(user_id=user_id, title=title, body=body))


def notify_all_managers(db: Session, zone_id: uuid.UUID | None, title: str, body: str) -> None:
    if zone_id:
        notify_zone_managers(db, zone_id, title, body)
    else:
        managers = db.scalars(
            select(User.id).where(User.role == Role.MUNICIPAL_OFFICER, User.deleted_at.is_(None))
        ).all()
        db.add_all(Notification(user_id=mid, title=title, body=body) for mid in managers)


def create_donation(db: Session, donor: User, payload: DonationCreate) -> ReuseListing:
    db_category = map_frontend_category(payload.category)
    db_condition = map_frontend_condition(payload.condition)

    desc = payload.description.strip() if payload.description else ""
    if payload.address:
        desc += f"\n\n[Pickup Location: {payload.address.strip()}]"

    listing = ReuseListing(
        lister_id=donor.id,
        zone_id=donor.zone_id,
        title=payload.title.strip(),
        category=db_category,
        description=desc if desc else None,
        condition=db_condition,
        status=ReuseStatus.PENDING_APPROVAL,
    )
    db.add(listing)
    db.flush()

    for idx, url in enumerate(payload.images, start=1):
        db.add(ReuseImage(listing_id=listing.id, img_url=url, sort_order=idx))

    # Notifications
    notify_user(
        db,
        donor.id,
        "Donation submitted",
        f"Your donation listing '{listing.title}' has been submitted for manager approval.",
    )

    ward_code = (
        db.scalar(select(Zone.code).where(Zone.id == donor.zone_id))
        if donor.zone_id
        else "Unassigned"
    )
    notify_all_managers(
        db,
        donor.zone_id,
        "New donation pending review",
        f"A new donation listing '{listing.title}' by {donor.name} "
        f"(Ward: {ward_code}) is pending review.",
    )

    db.commit()
    db.refresh(listing)
    return listing


def review_donation(
    db: Session, manager: User, listing_id: uuid.UUID, payload: DonationReview
) -> ReuseListing:
    listing = db.scalar(
        select(ReuseListing)
        .where(ReuseListing.id == listing_id)
        .options(joinedload(ReuseListing.lister))
    )
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Donation listing not found."
        )

    # Check manager ward permission
    managed_zone_ids = get_managed_zone_ids(db, manager)
    if listing.zone_id not in managed_zone_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Listing is outside your supervised wards.",
        )

    review_status = payload.status.upper()
    if review_status == "AVAILABLE":
        listing.status = ReuseStatus.AVAILABLE
        listing.reviewed_by_id = manager.id
        listing.rejection_reason = None
        notify_user(
            db,
            listing.lister_id,
            "Donation approved",
            f"Your donation listing '{listing.title}' has been approved "
            "and is now live on the Community Shelf.",
        )
    elif review_status == "REJECTED":
        reason = (payload.rejection_reason or "").strip()
        if not reason:
            raise HTTPException(
                status_code=422, detail="A rejection reason is required to reject a donation."
            )
        listing.status = ReuseStatus.REJECTED
        listing.reviewed_by_id = manager.id
        listing.rejection_reason = reason
        notify_user(
            db,
            listing.lister_id,
            "Donation rejected",
            f"Your donation listing '{listing.title}' was rejected "
            f"by the manager. Reason: {reason}",
        )
    else:
        raise HTTPException(status_code=422, detail=f"Invalid review status: {payload.status}")

    db.commit()
    db.refresh(listing)
    return listing


def claim_donation(db: Session, claimant: User, listing_id: uuid.UUID) -> ReuseListing:
    listing = db.scalar(
        select(ReuseListing)
        .where(ReuseListing.id == listing_id)
        .options(joinedload(ReuseListing.lister))
    )
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Donation listing not found."
        )

    if listing.status != ReuseStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only available items on the Community Shelf can be claimed.",
        )

    if listing.lister_id == claimant.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You cannot claim your own donation listing.",
        )

    # Check if this claimant already has a pending claim on this listing
    existing = db.scalar(
        select(ReuseClaim).where(
            ReuseClaim.listing_id == listing_id,
            ReuseClaim.claimant_id == claimant.id,
            ReuseClaim.status == ReuseClaimStatus.PENDING,
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already requested to claim this item.",
        )

    listing.status = ReuseStatus.CLAIM_PENDING
    claim = ReuseClaim(
        listing_id=listing.id, claimant_id=claimant.id, status=ReuseClaimStatus.PENDING
    )
    db.add(claim)

    notify_all_managers(
        db,
        listing.zone_id,
        "New claim request",
        f"Citizen {claimant.name} has requested to claim '{listing.title}'.",
    )

    db.commit()
    db.refresh(listing)
    return listing


def review_claim(
    db: Session, manager: User, claim_id: uuid.UUID, payload: ClaimReview
) -> ReuseClaim:
    claim = db.scalar(
        select(ReuseClaim)
        .where(ReuseClaim.id == claim_id)
        .options(
            joinedload(ReuseClaim.listing).joinedload(ReuseListing.lister),
            joinedload(ReuseClaim.claimant),
        )
    )
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Claim request not found."
        )

    listing = claim.listing

    # Check manager ward permission
    managed_zone_ids = get_managed_zone_ids(db, manager)
    if listing.zone_id not in managed_zone_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Claim is for a listing outside your supervised wards.",
        )

    review_status = payload.status.upper()
    now = datetime.now(UTC)

    if review_status == "APPROVED":
        claim.status = ReuseClaimStatus.APPROVED
        claim.decided_by_id = manager.id
        claim.decided_at = now
        claim.note = (payload.note or "").strip() or None

        listing.status = ReuseStatus.COMPLETED

        # Reject all other pending claims on this listing
        db.execute(
            update(ReuseClaim)
            .where(
                ReuseClaim.listing_id == listing.id,
                ReuseClaim.id != claim.id,
                ReuseClaim.status == ReuseClaimStatus.PENDING,
            )
            .values(
                status=ReuseClaimStatus.REJECTED,
                decided_by_id=manager.id,
                decided_at=now,
                note="Another claim was approved.",
            )
        )

        # Notify donor and claimant
        notify_user(
            db,
            listing.lister_id,
            "Donation claimed",
            f"Your donation listing '{listing.title}' has been successfully "
            f"claimed by {claim.claimant.name}.",
        )
        notify_user(
            db,
            claim.claimant_id,
            "Claim request approved",
            f"Your claim for '{listing.title}' has been approved! "
            "You can coordinate pickup with the donor.",
        )
    elif review_status == "REJECTED":
        note = (payload.note or "").strip()
        if not note:
            raise HTTPException(
                status_code=422, detail="A rejection note is required to reject a claim."
            )
        claim.status = ReuseClaimStatus.REJECTED
        claim.decided_by_id = manager.id
        claim.decided_at = now
        claim.note = note

        # Return listing status to AVAILABLE so others can claim
        listing.status = ReuseStatus.AVAILABLE

        # Notify claimant with note
        notify_user(
            db,
            claim.claimant_id,
            "Claim request rejected",
            f"Your claim for '{listing.title}' was rejected by the manager. Reason: {note}",
        )
    else:
        raise HTTPException(status_code=422, detail=f"Invalid review status: {payload.status}")

    db.commit()
    db.refresh(claim)
    return claim


def list_shelf_items(
    db: Session, current_user_id: uuid.UUID, search: str = "", category: str = ""
) -> list[ReuseListing]:
    query = (
        select(ReuseListing)
        .where(
            ReuseListing.status == ReuseStatus.AVAILABLE, ReuseListing.lister_id != current_user_id
        )
        .options(joinedload(ReuseListing.lister), joinedload(ReuseListing.images))
        .order_by(ReuseListing.created_at.desc())
    )

    if category:
        db_cat = map_frontend_category(category)
        query = query.where(ReuseListing.category == db_cat)

    if search:
        search_like = f"%{search.strip()}%"
        query = query.where(
            ReuseListing.title.ilike(search_like) | ReuseListing.description.ilike(search_like)
        )

    return db.scalars(query).unique().all()


def list_my_donations(db: Session, user_id: uuid.UUID) -> list[ReuseListing]:
    # Need to load the claimant info if someone requested claim
    # We join with claims and filter for the active claim (PENDING or APPROVED)
    query = (
        select(ReuseListing)
        .where(ReuseListing.lister_id == user_id)
        .options(
            joinedload(ReuseListing.images),
            joinedload(ReuseListing.claims).joinedload(ReuseClaim.claimant),
        )
        .order_by(ReuseListing.created_at.desc())
    )
    return db.scalars(query).unique().all()


def list_my_claims(db: Session, user_id: uuid.UUID, filter_status: str = "") -> list[ReuseClaim]:
    # Finds claims that the user submitted
    query = (
        select(ReuseClaim)
        .join(ReuseClaim.listing)
        .where(ReuseClaim.claimant_id == user_id)
        .options(
            joinedload(ReuseClaim.listing).joinedload(ReuseListing.images),
            joinedload(ReuseClaim.listing).joinedload(ReuseListing.lister),
            joinedload(ReuseClaim.claimant),
        )
        .order_by(ReuseClaim.created_at.desc())
    )
    if filter_status:
        if filter_status == "CLAIM_REQUESTED":
            query = query.where(ReuseClaim.status == ReuseClaimStatus.PENDING)
        elif filter_status == "COMPLETED":
            query = query.where(ReuseClaim.status == ReuseClaimStatus.APPROVED)
        elif filter_status == "REJECTED":
            query = query.where(ReuseClaim.status == ReuseClaimStatus.REJECTED)

    return db.scalars(query).unique().all()


def list_manager_pending_donations(db: Session, manager: User) -> list[ReuseListing]:
    managed_zone_ids = get_managed_zone_ids(db, manager)
    query = (
        select(ReuseListing)
        .where(ReuseListing.status == ReuseStatus.PENDING_APPROVAL)
        .options(joinedload(ReuseListing.lister), joinedload(ReuseListing.images))
        .order_by(ReuseListing.created_at.desc())
    )
    if managed_zone_ids:
        query = query.where(ReuseListing.zone_id.in_(managed_zone_ids))
    return db.scalars(query).unique().all()


def list_manager_pending_claims(db: Session, manager: User) -> list[ReuseClaim]:
    managed_zone_ids = get_managed_zone_ids(db, manager)
    query = (
        select(ReuseClaim)
        .join(ReuseClaim.listing)
        .where(ReuseClaim.status == ReuseClaimStatus.PENDING)
        .options(
            joinedload(ReuseClaim.listing).joinedload(ReuseListing.lister),
            joinedload(ReuseClaim.claimant),
        )
        .order_by(ReuseClaim.created_at.desc())
    )
    if managed_zone_ids:
        query = query.where(ReuseListing.zone_id.in_(managed_zone_ids))
    return db.scalars(query).unique().all()


def list_manager_all_donations(db: Session, manager: User) -> list[ReuseListing]:
    managed_zone_ids = get_managed_zone_ids(db, manager)
    query = (
        select(ReuseListing)
        .options(
            joinedload(ReuseListing.lister),
            joinedload(ReuseListing.images),
            joinedload(ReuseListing.claims).joinedload(ReuseClaim.claimant),
        )
        .order_by(ReuseListing.created_at.desc())
    )
    if managed_zone_ids:
        query = query.where(ReuseListing.zone_id.in_(managed_zone_ids))
    return db.scalars(query).unique().all()
