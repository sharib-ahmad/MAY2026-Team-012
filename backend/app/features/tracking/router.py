from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.bulk_pickups.models import BulkPickupRequest
from app.features.collection_ops.models import Pickup
from app.features.complaints.models import Ticket
from app.features.tracking.schemas import PublicTrackingResponse
from app.features.tracking.service import track_bulk_pickup, track_pickup, track_ticket

router = APIRouter(prefix="/track", tags=["Public Tracking"])


@router.get("/{ref_code}", response_model=PublicTrackingResponse)
def track_by_reference(ref_code: str, db: Session = Depends(get_db)) -> PublicTrackingResponse:
    """Return a single item's progress without exposing user contact details."""

    reference = ref_code.strip().upper()
    if not reference:
        raise HTTPException(status_code=404, detail="Tracking reference not found.")

    ticket = db.scalar(select(Ticket).where(func.upper(Ticket.ref_code) == reference))
    if ticket:
        return track_ticket(ticket)

    bulk_pickup = db.scalar(
        select(BulkPickupRequest).where(func.upper(BulkPickupRequest.ref_code) == reference)
    )
    if bulk_pickup:
        return track_bulk_pickup(bulk_pickup)

    pickup = db.scalar(select(Pickup).where(func.upper(Pickup.ref_code) == reference))
    if pickup:
        return track_pickup(pickup)

    raise HTTPException(status_code=404, detail="Tracking reference not found.")
