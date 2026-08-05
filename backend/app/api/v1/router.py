from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.features.admin.router import router as admin_router
from app.features.auth.router import router as auth_router
from app.features.bulk_pickups.models import BulkPickupRequest
from app.features.bulk_pickups.router import router as bulk_pickups_router
from app.features.collection_ops.models import Pickup
from app.features.collection_ops.router import collector_router
from app.features.collection_ops.router import router as collection_ops_router
from app.features.collection_ops.schemas import PublicTrackingResponse
from app.features.collection_ops.service import track_bulk_pickup, track_pickup, track_ticket
from app.features.complaints.models import Ticket
from app.features.complaints.router import router as complaints_router
from app.features.manager.router import router as manager_router
from app.features.materials.models import Batch
from app.features.materials.router import manager_router as materials_manager_router
from app.features.materials.router import recycler_router as materials_recycler_router
from app.features.notifications.router import router as notifications_router
from app.features.reuse.router import router as reuse_router
from app.features.users.router import router as user_router
from app.features.wards.router import router as wards_router
from app.models.zone import Zone

router = APIRouter()
router.include_router(auth_router, prefix="/auth")
router.include_router(user_router, prefix="/user")
router.include_router(bulk_pickups_router, prefix="/user")
router.include_router(complaints_router, prefix="/user")
router.include_router(collection_ops_router, prefix="/user")
router.include_router(collector_router)
router.include_router(notifications_router, prefix="/user")
router.include_router(wards_router)
router.include_router(admin_router, prefix="/admin")
router.include_router(manager_router)
router.include_router(materials_manager_router)
router.include_router(materials_recycler_router)
router.include_router(reuse_router)


@router.get("/track/{reference}", response_model=PublicTrackingResponse)
def track_by_reference(
    reference: str,
    db: Session = Depends(get_db),
) -> PublicTrackingResponse:
    reference = reference.strip().upper()

    ticket = db.scalar(
        select(Ticket)
        .where(func.upper(Ticket.ref_code) == reference)
        .options(
            joinedload(Ticket.raised_by),
            joinedload(Ticket.zone).joinedload(Zone.manager),
            joinedload(Ticket.zone).joinedload(Zone.members),
            joinedload(Ticket.resolved_by),
        )
    )
    if ticket:
        return track_ticket(ticket)

    bulk_pickup = db.scalar(
        select(BulkPickupRequest)
        .where(func.upper(BulkPickupRequest.ref_code) == reference)
        .options(
            joinedload(BulkPickupRequest.requester),
            joinedload(BulkPickupRequest.zone).joinedload(Zone.manager),
            joinedload(BulkPickupRequest.zone).joinedload(Zone.members),
            joinedload(BulkPickupRequest.decided_by),
            joinedload(BulkPickupRequest.assigned_collector),
        )
    )
    if bulk_pickup:
        # Search for corresponding pickup COL-<ref_code>
        pickup = db.scalar(
            select(Pickup)
            .where(func.upper(Pickup.ref_code) == "COL-" + reference)
            .options(
                joinedload(Pickup.citizen),
                joinedload(Pickup.zone).joinedload(Zone.manager),
                joinedload(Pickup.zone).joinedload(Zone.members),
                joinedload(Pickup.collector),
                joinedload(Pickup.batch).joinedload(Batch.destination_recycler),
                joinedload(Pickup.batch).joinedload(Batch.assigned_by),
            )
        )
        return track_bulk_pickup(bulk_pickup, pickup=pickup)

    pickup = db.scalar(
        select(Pickup)
        .where(func.upper(Pickup.ref_code) == reference)
        .options(
            joinedload(Pickup.citizen),
            joinedload(Pickup.zone).joinedload(Zone.manager),
            joinedload(Pickup.zone).joinedload(Zone.members),
            joinedload(Pickup.collector),
            joinedload(Pickup.batch).joinedload(Batch.destination_recycler),
            joinedload(Pickup.batch).joinedload(Batch.assigned_by),
        )
    )
    if pickup:
        return track_pickup(pickup)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Reference code not found.",
    )
