"""Batch pooling, assignment workflow, and credit awarding."""

from collections import defaultdict
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.features.bulk_pickups.models import BulkPickupRequest
from app.features.collection_ops.models import Pickup
from app.features.credits.models import Credit, CreditFactor
from app.features.manager.service import get_managed_zone_ids, notify_zone_managers
from app.features.materials.models import Batch
from app.features.notifications.models import Notification
from app.features.users.models import User
from app.models.enums import (
    BatchStatus,
    BulkRequestStatus,
    CreditReason,
    PickupStatus,
    Role,
    UserStatus,
)

BATCH_THRESHOLD_KG = 30.0


def _sync_bulk_pickup_status(db: Session, pickup: Pickup, status: BulkRequestStatus) -> None:
    """Sync BulkPickupRequest status when Pickup status changes."""
    prefix = "COL-"
    if not pickup.ref_code.startswith(prefix):
        return
    request = db.scalar(
        select(BulkPickupRequest).where(
            BulkPickupRequest.ref_code == pickup.ref_code[len(prefix) :]
        )
    )
    if request:
        request.status = status


def _next_batch_ref(db: Session) -> str:
    existing = db.scalar(select(func.count()).select_from(Batch)) or 0
    return f"BAT-{existing + 1:05d}"


def _pickup_weight(pickup: Pickup) -> float:
    weight = pickup.actual_weight if pickup.actual_weight is not None else pickup.estimated_weight
    return float(weight)


def _build_batch_groups(pickups: list[Pickup]) -> list[list[Pickup]]:
    """Create batches when total weight reaches 30kg or more."""
    remaining = list(pickups)
    groups: list[list[Pickup]] = []

    while remaining:
        group = []
        total = 0.0

        for pickup in sorted(remaining, key=_pickup_weight, reverse=True):
            weight = _pickup_weight(pickup)
            if total + weight >= BATCH_THRESHOLD_KG or not group:
                group.append(pickup)
                total += weight
                remaining.remove(pickup)
                if total >= BATCH_THRESHOLD_KG:
                    break

        if total >= BATCH_THRESHOLD_KG:
            groups.append(group)
        else:
            break

    return groups


def _resolve_collector_id(db: Session, zone_id: UUID, pickups: list[Pickup]) -> UUID:
    for pickup in reversed(pickups):
        if pickup.collector_id:
            return pickup.collector_id
    collector_id = db.scalar(
        select(User.id)
        .where(
            User.role == Role.COLLECTION_WORKER,
            User.zone_id == zone_id,
            User.deleted_at.is_(None),
            User.status == UserStatus.ACTIVE,
        )
        .limit(1)
    )
    if collector_id:
        return collector_id
    fallback = db.scalar(
        select(User.id)
        .where(
            User.role == Role.COLLECTION_WORKER,
            User.deleted_at.is_(None),
            User.status == UserStatus.ACTIVE,
        )
        .limit(1)
    )
    if not fallback:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No collector available to record this batch.",
        )
    return fallback


def pool_and_maybe_create_batches(db: Session, zone_id: UUID) -> list[Batch]:
    """Pool unbatched COLLECTED pickups and auto-create batches when ≥ 30 kg."""
    created: list[Batch] = []
    while True:
        pickups = db.scalars(
            select(Pickup)
            .where(
                Pickup.zone_id == zone_id,
                Pickup.status == PickupStatus.COLLECTED,
                Pickup.batch_id.is_(None),
            )
            .order_by(Pickup.completed_at.asc().nullslast(), Pickup.created_at)
        ).all()
        if not pickups:
            break

        by_category: dict[str, list[Pickup]] = defaultdict(list)
        for pickup in pickups:
            by_category[pickup.category].append(pickup)

        created_before = len(created)
        for category, cat_pickups in by_category.items():
            for group in _build_batch_groups(cat_pickups):
                total = sum(_pickup_weight(pickup) for pickup in group)
                now = datetime.now(UTC)
                batch = Batch(
                    ref_code=_next_batch_ref(db),
                    collector_id=_resolve_collector_id(db, zone_id, group),
                    assigned_by_id=None,
                    zone_id=zone_id,
                    status=BatchStatus.COLLECTED,
                    waste_category=category,
                    declared_weight=total,
                    collected_at=now,
                )
                db.add(batch)
                db.flush()
                for pickup in group:
                    pickup.batch_id = batch.id

                notify_zone_managers(
                    db,
                    zone_id,
                    "Batch ready for assignment",
                    (
                        f"Batch {batch.ref_code} ({category}, {total:.1f} kg) "
                        "is ready for recycler assignment."
                    ),
                )
                created.append(batch)

        if len(created) == created_before:
            break

    return created


def serialize_batch(batch: Batch) -> dict:
    recycler = batch.destination_recycler
    zone = batch.zone
    pickups = batch.pickups or []
    return {
        "id": batch.id,
        "ref_code": batch.ref_code,
        "status": batch.status.value,
        "waste_category": batch.waste_category,
        "declared_weight": float(batch.declared_weight),
        "final_weight": float(batch.final_weight) if batch.final_weight is not None else None,
        "quality_status": batch.quality_status.value if batch.quality_status else None,
        "contamination_note": batch.contamination_note,
        "rejection_reason": batch.rejection_reason,
        "remarks": batch.remarks,
        "zone_id": batch.zone_id,
        "zone_code": zone.code if zone else None,
        "zone_name": zone.name if zone else None,
        "destination_recycler_id": batch.destination_recycler_id,
        "destination_recycler_name": recycler.name if recycler else None,
        "pickup_count": len(pickups),
        "pickup_ref_codes": [pickup.ref_code for pickup in pickups],
        "collected_at": batch.collected_at,
        "assigned_at": batch.assigned_at,
        "rejected_at": batch.rejected_at,
        "processed_at": batch.processed_at,
        "created_at": batch.created_at,
        "updated_at": batch.updated_at,
    }


def _load_batch(db: Session, batch_id: UUID) -> Batch:
    batch = (
        db.scalars(
            select(Batch)
            .where(Batch.id == batch_id)
            .options(
                joinedload(Batch.zone),
                joinedload(Batch.destination_recycler),
                joinedload(Batch.pickups),
            )
        )
        .unique()
        .one_or_none()
    )
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found.")
    return batch


def list_manager_batches(db: Session, manager: User) -> list[dict]:
    zone_ids = get_managed_zone_ids(db, manager)
    if not zone_ids:
        return []
    batches = (
        db.scalars(
            select(Batch)
            .where(Batch.zone_id.in_(zone_ids))
            .options(
                joinedload(Batch.zone),
                joinedload(Batch.destination_recycler),
                joinedload(Batch.pickups),
            )
            .order_by(Batch.created_at.desc())
        )
        .unique()
        .all()
    )
    return [serialize_batch(batch) for batch in batches if batch.pickups and len(batch.pickups) > 0]


def list_recyclers(db: Session) -> list[dict]:
    recyclers = db.scalars(
        select(User)
        .where(
            User.role == Role.RECYCLER,
            User.deleted_at.is_(None),
            User.status == UserStatus.ACTIVE,
        )
        .order_by(User.name)
    ).all()
    return [
        {"id": recycler.id, "name": recycler.name, "email": recycler.email}
        for recycler in recyclers
    ]


def assign_batch(db: Session, manager: User, batch_id: UUID, recycler_id: UUID) -> dict:
    batch = _load_batch(db, batch_id)
    zone_ids = get_managed_zone_ids(db, manager)
    if zone_ids and batch.zone_id not in zone_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Batch is outside your wards.",
        )
    if batch.status != BatchStatus.COLLECTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only collected batches awaiting assignment can be assigned.",
        )

    recycler = db.scalar(
        select(User).where(
            User.id == recycler_id,
            User.role == Role.RECYCLER,
            User.status == UserStatus.ACTIVE,
            User.deleted_at.is_(None),
        )
    )
    if not recycler:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Choose an active recycler.",
        )

    now = datetime.now(UTC)
    batch.destination_recycler_id = recycler.id
    batch.assigned_by_id = manager.id
    batch.assigned_at = now
    batch.rejected_at = None
    batch.rejection_reason = None
    batch.status = BatchStatus.ASSIGNED
    for pickup in batch.pickups:
        pickup.status = PickupStatus.RECYCLER_ASSIGNED
        _sync_bulk_pickup_status(db, pickup, BulkRequestStatus.RECYCLER_ASSIGNED)
        db.add(
            Notification(
                user_id=pickup.citizen_id,
                title="Pickup assigned to recycler",
                body=(
                    f"Your pickup {pickup.ref_code} has been assigned to a recycler for processing."
                ),
            )
        )

    db.add(
        Notification(
            user_id=recycler.id,
            title="Batch assigned to you",
            body=f"Batch {batch.ref_code} ({batch.waste_category}) awaits your review.",
        )
    )
    db.commit()
    db.refresh(batch)
    return serialize_batch(batch)


def list_recycler_batches(db: Session, recycler: User, statuses: set[BatchStatus]) -> list[dict]:
    batches = (
        db.scalars(
            select(Batch)
            .where(
                Batch.destination_recycler_id == recycler.id,
                Batch.status.in_(statuses),
            )
            .options(
                joinedload(Batch.zone),
                joinedload(Batch.destination_recycler),
                joinedload(Batch.pickups),
            )
            .order_by(Batch.updated_at.desc())
        )
        .unique()
        .all()
    )
    # Filter out batches with 0 pickups
    return [serialize_batch(batch) for batch in batches if batch.pickups and len(batch.pickups) > 0]


def accept_batch(db: Session, recycler: User, batch_id: UUID) -> dict:
    batch = _load_batch(db, batch_id)
    if batch.destination_recycler_id != recycler.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Batch not assigned to you.",
        )
    if batch.status != BatchStatus.ASSIGNED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only assigned batches can be accepted.",
        )

    batch.status = BatchStatus.PROCESSING
    batch.rejected_at = None
    batch.rejection_reason = None
    for pickup in batch.pickups:
        pickup.status = PickupStatus.PROCESSING
        _sync_bulk_pickup_status(db, pickup, BulkRequestStatus.PROCESSING)
        db.add(
            Notification(
                user_id=pickup.citizen_id,
                title="Pickup processing started",
                body=f"Your pickup {pickup.ref_code} is now being processed by the recycler.",
            )
        )
    db.commit()
    db.refresh(batch)
    return serialize_batch(batch)


def reject_batch(db: Session, recycler: User, batch_id: UUID, note: str) -> dict:
    batch = _load_batch(db, batch_id)
    if batch.destination_recycler_id != recycler.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Batch not assigned to you.",
        )
    if batch.status != BatchStatus.ASSIGNED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only assigned batches can be rejected.",
        )

    now = datetime.now(UTC)
    batch.status = BatchStatus.COLLECTED
    batch.rejected_at = now
    batch.rejection_reason = note.strip()
    batch.destination_recycler_id = None
    batch.assigned_at = None
    for pickup in batch.pickups:
        pickup.status = PickupStatus.COLLECTED
        _sync_bulk_pickup_status(db, pickup, BulkRequestStatus.COLLECTED)

    if batch.zone_id:
        notify_zone_managers(
            db,
            batch.zone_id,
            "Batch rejected by recycler",
            (
                f"Batch {batch.ref_code} was rejected by {recycler.name}. "
                f"Note: {batch.rejection_reason}"
            ),
        )

    db.commit()
    db.refresh(batch)
    return serialize_batch(batch)


def _award_pickup_credit(db: Session, pickup: Pickup, processed_at: datetime) -> None:
    try:
        factor = db.scalar(select(CreditFactor).where(CreditFactor.category == pickup.category))
        weight = _pickup_weight(pickup)

        # Handle missing CreditFactor gracefully
        if factor:
            rate = float(factor.credit_rate)
            co2_factor = float(factor.co2_factor)
        else:
            rate = 0.0
            co2_factor = 0.0

        amount = round(weight * rate, 2)
        co2_saved = round(weight * co2_factor, 3)

        existing = db.scalar(
            select(Credit).where(
                Credit.pickup_id == pickup.id,
                Credit.reason == CreditReason.PICKUP_RECYCLING,
            )
        )
        if not existing:
            if not pickup.citizen_id:
                raise ValueError(f"Pickup {pickup.ref_code} has no citizen_id")
            db.add(
                Credit(
                    user_id=pickup.citizen_id,
                    pickup_id=pickup.id,
                    amount=amount,
                    co2_saved=co2_saved,
                    reason=CreditReason.PICKUP_RECYCLING,
                )
            )

        pickup.credit_rate_applied = rate
        pickup.co2_factor_applied = co2_factor
        pickup.credits_earned = amount
        pickup.co2_saved = co2_saved
        pickup.status = PickupStatus.PROCESSED
        pickup.completed_at = processed_at
        _sync_bulk_pickup_status(db, pickup, BulkRequestStatus.PROCESSED)

        if pickup.citizen_id:
            db.add(
                Notification(
                    user_id=pickup.citizen_id,
                    title="Recycling reward credited",
                    body=(
                        f"Your pickup {pickup.ref_code} was processed. "
                        f"You earned {amount:.2f} green credits."
                    ),
                )
            )
    except HTTPException:
        raise
    except Exception as e:
        import traceback

        error_detail = (
            f"Error awarding credit for pickup {pickup.ref_code} "
            f"(category: {pickup.category}): {str(e)}\n{traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail,
        ) from e


def process_batch(db: Session, recycler: User, batch_id: UUID) -> dict:
    batch = _load_batch(db, batch_id)

    if batch.destination_recycler_id != recycler.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Batch not assigned to you.",
        )
    if batch.status != BatchStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only processing batches can be marked processed.",
        )
    if not batch.pickups:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot process a batch with no pickups.",
        )

    now = datetime.now(UTC)
    batch.status = BatchStatus.PROCESSED
    batch.processed_at = now
    batch.processed_quantity = float(batch.declared_weight)

    # Award credits, update co2, set pickup status, sync bulk request status,
    # and notify citizens — _award_pickup_credit handles all of this.
    for pickup in batch.pickups:
        _award_pickup_credit(db, pickup, now)

    db.add(
        Notification(
            user_id=recycler.id,
            title="Batch marked processed",
            body=f"Batch {batch.ref_code} has been successfully processed.",
        )
    )

    db.commit()
    db.refresh(batch)
    return serialize_batch(batch)
