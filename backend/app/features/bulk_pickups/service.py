import uuid

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.features.bulk_pickups.models import BulkPickupRequest
from app.features.bulk_pickups.schemas import (
    PickupResponse,
    PickupTrackingResponse,
    TrackingEvent,
)
from app.models.enums import BulkRequestStatus


def citizen_requests(user_id: uuid.UUID):
    return (
        select(BulkPickupRequest)
        .where(BulkPickupRequest.requester_id == user_id)
        .options(
            joinedload(BulkPickupRequest.zone),
            joinedload(BulkPickupRequest.waste_category),
            joinedload(BulkPickupRequest.assigned_collector),
        )
    )


def serialize_request(request: BulkPickupRequest) -> PickupResponse:
    category = request.waste_category.label if request.waste_category else request.category
    return PickupResponse(
        id=request.id,
        ref_code=request.ref_code,
        category=category,
        estimated_weight=float(request.estimated_weight or 0),
        scheduled_date=request.requested_date,
        time_slot=request.time_slot,
        notes=request.notes,
        status=request.status.value,
        zone_name=f"{request.zone.code} - {request.zone.name}" if request.zone else None,
        collector_name=request.assigned_collector.name if request.assigned_collector else None,
        collector_phone=request.assigned_collector.phone if request.assigned_collector else None,
        is_flagged=request.is_flagged,
        flag_severity=request.flag_severity.value if request.flag_severity else None,
        flag_note=request.flag_note,
        created_at=request.created_at,
    )


def build_tracking_response(request: BulkPickupRequest) -> PickupTrackingResponse:
    timeline = [
        TrackingEvent(stage="PENDING", label="Pickup request submitted", at=request.created_at)
    ]
    if request.status != BulkRequestStatus.PENDING:
        timeline.append(
            TrackingEvent(
                stage=request.status.value,
                label=f"Request {request.status.value.lower()}",
                at=request.updated_at,
            )
        )
    return PickupTrackingResponse(
        ref_code=request.ref_code,
        status=request.status.value,
        stops_remaining=0,
        estimated_arrival=request.time_slot,
        timeline=timeline,
    )
