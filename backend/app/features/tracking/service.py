from app.features.bulk_pickups.models import BulkPickupRequest
from app.features.collection_ops.models import Pickup
from app.features.complaints.models import Ticket
from app.features.tracking.schemas import PublicTrackingEvent, PublicTrackingResponse


def _event(stage: str, label: str, at) -> PublicTrackingEvent:
    return PublicTrackingEvent(stage=stage, label=label, at=at)


def track_ticket(ticket: Ticket) -> PublicTrackingResponse:
    timeline = [_event("OPEN", "Complaint submitted", ticket.created_at)]
    if ticket.status.value != "OPEN":
        label = "Complaint resolved" if ticket.status.value == "RESOLVED" else "Complaint status updated"
        timeline.append(_event(ticket.status.value, label, ticket.updated_at))
    return PublicTrackingResponse(
        ref_code=ticket.ref_code,
        entity_type="TICKET",
        status=ticket.status.value,
        issue_type=ticket.issue_type.value,
        created_at=ticket.created_at,
        last_updated=ticket.updated_at,
        timeline=timeline,
    )


def track_bulk_pickup(request: BulkPickupRequest) -> PublicTrackingResponse:
    timeline = [_event("PENDING", "Pickup request submitted", request.created_at)]
    if request.status.value != "PENDING":
        timeline.append(
            _event(request.status.value, f"Pickup {request.status.value.lower()}", request.updated_at)
        )
    return PublicTrackingResponse(
        ref_code=request.ref_code,
        entity_type="PICKUP",
        status=request.status.value,
        category=request.category,
        scheduled_date=request.requested_date,
        created_at=request.created_at,
        last_updated=request.updated_at,
        timeline=timeline,
    )


def track_pickup(pickup: Pickup) -> PublicTrackingResponse:
    timeline = [_event("PENDING", "Pickup request submitted", pickup.created_at)]
    if pickup.status.value != "PENDING":
        timeline.append(
            _event(pickup.status.value, f"Pickup {pickup.status.value.lower()}", pickup.updated_at)
        )
    return PublicTrackingResponse(
        ref_code=pickup.ref_code,
        entity_type="PICKUP",
        status=pickup.status.value,
        category=pickup.category,
        scheduled_date=pickup.scheduled_date,
        created_at=pickup.created_at,
        last_updated=pickup.updated_at,
        timeline=timeline,
    )
