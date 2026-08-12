from app.features.bulk_pickups.models import BulkPickupRequest
from app.features.collection_ops.models import Pickup
from app.features.collection_ops.schemas import PublicTrackingEvent, PublicTrackingResponse
from app.features.complaints.models import Ticket
from app.models.enums import BatchStatus, PickupStatus


def _event(stage: str, label: str, at) -> PublicTrackingEvent:
    return PublicTrackingEvent(stage=stage, label=label, at=at)


def _resolve_manager_name(zone, default_manager_name=None) -> str | None:
    if default_manager_name:
        return (
            default_manager_name.name
            if hasattr(default_manager_name, "name")
            else default_manager_name
        )
    if zone:
        # 1. Try Zone.manager relationship (if populated)
        manager = getattr(zone, "manager", None)
        if manager and getattr(manager, "name", None):
            return manager.name
        # 2. Fallback: Search Zone.members for a user with role MUNICIPAL_OFFICER
        members = getattr(zone, "members", []) or []
        for m in members:
            role_val = getattr(getattr(m, "role", None), "value", None) or getattr(m, "role", None)
            if role_val == "MUNICIPAL_OFFICER":
                return m.name
    return None


def track_ticket(ticket: Ticket) -> PublicTrackingResponse:
    timeline = [_event("OPEN", "Complaint submitted", ticket.created_at)]
    if ticket.status.value != "OPEN":
        label = (
            "Complaint resolved"
            if ticket.status.value == "RESOLVED"
            else "Complaint status updated"
        )
        timeline.append(_event(ticket.status.value, label, ticket.updated_at))

    raised_by = getattr(ticket, "raised_by", None)
    zone = getattr(ticket, "zone", None)
    resolved_by = getattr(ticket, "resolved_by", None)

    manager_name = _resolve_manager_name(zone, resolved_by)

    return PublicTrackingResponse(
        ref_code=ticket.ref_code,
        entity_type="TICKET",
        status=ticket.status.value,
        issue_type=ticket.issue_type.value,
        created_at=ticket.created_at,
        last_updated=ticket.updated_at,
        timeline=timeline,
        citizen_name=raised_by.name if raised_by else None,
        zone_name=zone.name if zone else None,
        manager_name=manager_name,
    )


def track_bulk_pickup(
    request: BulkPickupRequest,
    pickup: Pickup | None = None,
) -> PublicTrackingResponse:
    if pickup:
        res = track_pickup(pickup)
        return PublicTrackingResponse(
            ref_code=request.ref_code,
            entity_type=res.entity_type,
            status=res.status,
            category=res.category,
            issue_type=res.issue_type,
            scheduled_date=res.scheduled_date,
            created_at=res.created_at,
            last_updated=res.last_updated,
            timeline=res.timeline,
            citizen_name=res.citizen_name,
            zone_name=res.zone_name,
            manager_name=res.manager_name,
            collector_name=res.collector_name,
            recycler_name=res.recycler_name,
        )

    timeline = [_event("PENDING", "Pickup request submitted", request.created_at)]
    if request.status.value != "PENDING":
        status_val = request.status.value
        stage_key = status_val
        if status_val == "ASSIGNED":
            stage_key = "SCHEDULED"
            label = "Collector assigned"
        elif status_val == "APPROVED":
            stage_key = "SCHEDULED"
            label = "Pickup request approved"
        elif status_val == "RECYCLER_ASSIGNED":
            stage_key = "ASSIGNED"
            label = "Assigned to recycler"
        else:
            label = f"Pickup {status_val.lower()}"

        timeline.append(
            _event(
                stage_key,
                label,
                request.updated_at,
            )
        )

    requester = getattr(request, "requester", None)
    zone = getattr(request, "zone", None)
    decided_by = getattr(request, "decided_by", None)
    assigned_collector = getattr(request, "assigned_collector", None)

    manager_name = _resolve_manager_name(zone, decided_by)

    return PublicTrackingResponse(
        ref_code=request.ref_code,
        entity_type="PICKUP",
        status=request.status.value,
        category=request.category,
        scheduled_date=request.requested_date,
        created_at=request.created_at,
        last_updated=request.updated_at,
        timeline=timeline,
        citizen_name=requester.name if requester else None,
        zone_name=zone.name if zone else None,
        manager_name=manager_name,
        collector_name=assigned_collector.name if assigned_collector else None,
    )


def track_pickup(pickup: Pickup) -> PublicTrackingResponse:
    timeline = [_event("PENDING", "Pickup request submitted", pickup.created_at)]

    if pickup.scheduled_date:
        timeline.append(_event("SCHEDULED", "Pickup scheduled", pickup.scheduled_date))

    if pickup.status.value not in {PickupStatus.PENDING.value, PickupStatus.SCHEDULED.value}:
        collected_at = pickup.completed_at or pickup.updated_at
        if pickup.status.value in {
            PickupStatus.COLLECTED.value,
            PickupStatus.RECYCLER_ASSIGNED.value,
            PickupStatus.PROCESSING.value,
            PickupStatus.PROCESSED.value,
            PickupStatus.COMPLETED.value,
        }:
            timeline.append(_event("COLLECTED", "Pickup collected", collected_at))

    batch = pickup.batch
    if batch:
        timeline.append(
            _event(
                "BATCHED",
                f"Added to batch {batch.ref_code}",
                batch.collected_at or batch.created_at,
            )
        )
        if batch.assigned_at or batch.status in {
            BatchStatus.ASSIGNED,
            BatchStatus.PROCESSING,
            BatchStatus.PROCESSED,
        }:
            timeline.append(
                _event(
                    "ASSIGNED",
                    "Assigned to recycler",
                    batch.assigned_at or batch.updated_at,
                )
            )
        if batch.status in {BatchStatus.PROCESSING, BatchStatus.PROCESSED}:
            timeline.append(
                _event(
                    "PROCESSING",
                    "Recycler processing batch",
                    batch.updated_at,
                )
            )
        if batch.processed_at or batch.status == BatchStatus.PROCESSED:
            timeline.append(
                _event(
                    "PROCESSED",
                    "Batch processed",
                    batch.processed_at or batch.updated_at,
                )
            )

    if pickup.status in {PickupStatus.PROCESSED, PickupStatus.COMPLETED} and pickup.credits_earned:
        timeline.append(
            _event(
                "CREDITED",
                f"Recycling reward credited ({pickup.credits_earned:.2f} credits)",
                pickup.updated_at,
            )
        )

    citizen = getattr(pickup, "citizen", None)
    zone = getattr(pickup, "zone", None)
    collector = getattr(pickup, "collector", None)
    batch = getattr(pickup, "batch", None)

    assigned_by = getattr(batch, "assigned_by", None) if batch else None
    recycler = getattr(batch, "destination_recycler", None) if batch else None

    manager_name = _resolve_manager_name(zone, assigned_by)

    return PublicTrackingResponse(
        ref_code=pickup.ref_code,
        entity_type="PICKUP",
        status=pickup.status.value,
        category=pickup.category,
        scheduled_date=pickup.scheduled_date,
        created_at=pickup.created_at,
        last_updated=pickup.updated_at,
        timeline=timeline,
        citizen_name=citizen.name if citizen else None,
        zone_name=zone.name if zone else None,
        manager_name=manager_name,
        collector_name=collector.name if collector else None,
        recycler_name=recycler.name if recycler else None,
    )
