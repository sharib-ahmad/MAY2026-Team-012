import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.bulk_pickups.models import BulkPickupRequest
from app.features.bulk_pickups.schemas import (
    PickupCreate,
    PickupResponse,
    PickupsResponse,
    PickupTrackingResponse,
)
from app.features.bulk_pickups.service import (
    build_tracking_response,
    resident_requests,
    serialize_request,
)
from app.features.manager.service import notify_zone_managers
from app.features.notifications.models import Notification
from app.features.sorting_guide.models import WasteCategory
from app.features.users.dependencies import require_resident
from app.features.users.models import User
from app.models.enums import BulkRequestStatus

router = APIRouter(tags=["Resident Pickups"])


@router.get("/pickups", response_model=PickupsResponse)
def list_pickups(
    current_user: User = Depends(require_resident), db: Session = Depends(get_db)
) -> PickupsResponse:
    requests = (
        db.scalars(resident_requests(current_user.id).order_by(BulkPickupRequest.created_at.desc()))
        .unique()
        .all()
    )
    return PickupsResponse(
        pickups=[serialize_request(request) for request in requests], total=len(requests)
    )


@router.post("/pickups", response_model=PickupResponse, status_code=status.HTTP_201_CREATED)
def create_pickup(
    payload: PickupCreate,
    current_user: User = Depends(require_resident),
    db: Session = Depends(get_db),
) -> PickupResponse:
    if not current_user.zone_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Assign a ward before scheduling a pickup.",
        )
    category = db.scalar(
        select(WasteCategory).where(
            WasteCategory.code == payload.category, WasteCategory.is_active.is_(True)
        )
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid waste category."
        )
    if payload.scheduled_date < datetime.now(UTC) + timedelta(hours=24):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Pickup requests require at least 24 hours' notice.",
        )
    request = BulkPickupRequest(
        ref_code=f"BPR-{uuid.uuid4().hex[:8].upper()}",
        requester_id=current_user.id,
        zone_id=current_user.zone_id,
        category=category.code,
        requested_date=payload.scheduled_date,
        estimated_weight=payload.estimated_weight,
        time_slot=payload.time_slot,
        notes=payload.notes,
        status=BulkRequestStatus.PENDING,
    )
    db.add(request)
    db.add(
        Notification(
            user_id=current_user.id,
            title="Pickup scheduled",
            body=(
                f"Your pickup {request.ref_code} is scheduled for "
                f"{request.requested_date:%d %b %Y}."
            ),
        )
    )
    notify_zone_managers(
        db,
        request.zone_id,
        "New bulk pickup request",
        f"{request.ref_code} needs collection on {request.requested_date:%d %b %Y}.",
    )
    db.commit()
    request = db.scalar(
        resident_requests(current_user.id).where(BulkPickupRequest.id == request.id)
    )
    return serialize_request(request)


@router.patch("/pickups/{pickup_id}/cancel", response_model=PickupResponse)
def cancel_pickup(
    pickup_id: uuid.UUID,
    current_user: User = Depends(require_resident),
    db: Session = Depends(get_db),
) -> PickupResponse:
    request = db.scalar(resident_requests(current_user.id).where(BulkPickupRequest.id == pickup_id))
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pickup not found.")
    if request.status not in {BulkRequestStatus.PENDING, BulkRequestStatus.APPROVED}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This pickup can no longer be cancelled."
        )
    request.status = BulkRequestStatus.CANCELLED
    db.commit()
    return serialize_request(request)


@router.get("/pickups/{pickup_id}/tracking", response_model=PickupTrackingResponse)
def pickup_tracking(
    pickup_id: uuid.UUID,
    current_user: User = Depends(require_resident),
    db: Session = Depends(get_db),
) -> PickupTrackingResponse:
    request = db.scalar(resident_requests(current_user.id).where(BulkPickupRequest.id == pickup_id))
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pickup not found.")
    return build_tracking_response(request)
