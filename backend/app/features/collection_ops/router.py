import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.config import get_settings
from app.features.collection_ops.ors_client import ORSClient

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, or_, select, update
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.features.bulk_pickups.models import BulkPickupRequest
from app.features.collection_ops.models import (
    DailyPickupSchedule,
    DailyPickupStop,
    DelayLog,
    MixedWasteTag,
    Pickup,
)
from app.features.collection_ops.schemas import (
    CollectorRouteResponse,
    CollectorStopResponse,
    DailyPickupScheduleResponse,
    DelayStopRequest,
    MixedWasteRequest,
)
from app.features.manager.service import notify_zone_managers
from app.features.materials.service import pool_and_maybe_create_batches
from app.features.notifications.models import Notification
from app.features.notifications.service import list_for_user, mark_read
from app.features.users.dependencies import require_citizen, require_collector
from app.features.users.models import User
from app.models.enums import BulkRequestStatus, PickupStatus, PickupStopStatus, WasteSeverity

router = APIRouter(tags=["Citizen Collection Schedules"])
collector_router = APIRouter(prefix="/collector", tags=["Collector Operations"])


@router.get("/daily-pickup-schedules", response_model=list[DailyPickupScheduleResponse])
def list_daily_pickup_schedules(
    current_user: User = Depends(require_citizen), db: Session = Depends(get_db)
) -> list[DailyPickupScheduleResponse]:
    stops = (
        db.scalars(
            select(DailyPickupStop)
            .where(DailyPickupStop.citizen_id == current_user.id)
            .join(DailyPickupStop.schedule)
            .options(joinedload(DailyPickupStop.schedule).joinedload(DailyPickupSchedule.collector))
            .order_by(DailyPickupSchedule.schedule_date.desc())
        )
        .unique()
        .all()
    )
    return [
        DailyPickupScheduleResponse(
            schedule_id=stop.schedule.id,
            schedule_date=stop.schedule.schedule_date,
            collector_name=stop.schedule.collector.name if stop.schedule.collector else None,
            pickup_order=stop.pickup_order,
            stop_status=stop.status.value,
            total_stops=stop.schedule.total_stops,
            completed_stops=stop.schedule.completed_stops,
        )
        for stop in stops
    ]


def _collector_stop(
    stop: DailyPickupStop, pickup_order: int | None = None, is_flagged: bool | None = None
) -> CollectorStopResponse:
    return CollectorStopResponse(
        id=stop.id,
        ref_code=stop.pickup.ref_code,
        status=stop.status.value,
        pickup_order=pickup_order if pickup_order is not None else stop.pickup_order,
        citizen_name=stop.citizen.name,
        category=stop.pickup.category,
        estimated_weight=float(stop.pickup.estimated_weight),
        pickup_address=stop.notes,
        zone_name=stop.schedule.zone.name,
        time_slot=stop.pickup.time_slot,
        pickup_latitude=stop.latitude,
        pickup_longitude=stop.longitude,
        completed_at=stop.completed_at,
        is_flagged=bool(getattr(stop, "mixed_waste_tags", []))
        if is_flagged is None
        else is_flagged,
    )


def _bulk_pickup_response(
    pickup: BulkPickupRequest, pickup_order: int, is_flagged: bool | None = None
) -> CollectorStopResponse:
    return CollectorStopResponse(
        id=pickup.id,
        ref_code=pickup.ref_code,
        status=pickup.status.value,
        pickup_order=pickup_order,
        citizen_name=pickup.requester.name,
        category=pickup.category,
        estimated_weight=float(pickup.estimated_weight or 0),
        pickup_address=pickup.notes,
        zone_name=f"{pickup.zone.code} - {pickup.zone.name}",
        time_slot=pickup.time_slot,
        pickup_latitude=pickup.requester.latitude,
        pickup_longitude=pickup.requester.longitude,
        completed_at=pickup.collected_at,
        is_flagged=pickup.is_flagged if is_flagged is None else is_flagged,
    )


def _owned_bulk_pickup(db: Session, pickup_id: UUID, collector_id: UUID) -> BulkPickupRequest:
    pickup = db.scalar(
        select(BulkPickupRequest)
        .where(
            BulkPickupRequest.id == pickup_id,
            BulkPickupRequest.assigned_collector_id == collector_id,
        )
        .options(joinedload(BulkPickupRequest.requester), joinedload(BulkPickupRequest.zone))
    )
    if not pickup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned pickup not found.",
        )
    return pickup


def _owned_stop(db: Session, stop_id: UUID, collector_id: UUID) -> DailyPickupStop:
    stop = db.scalar(
        select(DailyPickupStop)
        .join(DailyPickupStop.schedule)
        .join(DailyPickupStop.pickup)
        .where(
            DailyPickupStop.id == stop_id,
            DailyPickupSchedule.collector_id == collector_id,
            Pickup.ref_code.like("COL-%"),
        )
        .options(
            joinedload(DailyPickupStop.pickup),
            joinedload(DailyPickupStop.citizen),
            joinedload(DailyPickupStop.schedule).joinedload(DailyPickupSchedule.zone),
        )
    )
    if not stop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned pickup not found.",
        )
    return stop


def _refresh_schedule_completion(schedule: DailyPickupSchedule, db: Session) -> None:
    stops = db.scalars(
        select(DailyPickupStop).where(DailyPickupStop.schedule_id == schedule.id)
    ).all()
    schedule.completed_stops = sum(stop.status == PickupStopStatus.COLLECTED for stop in stops)
    schedule.completed_at = (
        datetime.now(UTC) if stops and schedule.completed_stops == len(stops) else None
    )


def _day_bounds(now: datetime | None = None) -> tuple[datetime, datetime]:
    now = now or datetime.now(UTC)
    start = now.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)


def _ensure_not_collected(stop: DailyPickupStop) -> None:
    if stop.status == PickupStopStatus.COLLECTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This pickup is already collected.",
        )


def _sync_source_bulk_pickup(
    db: Session,
    stop: DailyPickupStop,
    status_value: BulkRequestStatus,
    collected_at: datetime | None,
    *,
    is_flagged: bool | None = None,
    flag_severity: WasteSeverity | None = None,
    flag_note: str | None = None,
) -> None:
    """Reflect route-stop completion in the citizen/manager source request."""
    prefix = "COL-"
    if not stop.pickup.ref_code.startswith(prefix):
        return
    request = db.scalar(
        select(BulkPickupRequest).where(
            BulkPickupRequest.ref_code == stop.pickup.ref_code[len(prefix) :]
        )
    )
    if request:
        request.status = status_value
        request.collected_at = collected_at
        if is_flagged is not None:
            request.is_flagged = is_flagged
            request.flag_severity = flag_severity
            request.flag_note = flag_note


def _is_within_undo_window(completed_at: datetime | None) -> bool:
    if not completed_at:
        return False
    # SQLite test databases may round-trip timezone-aware datetimes as naive.
    completed_at = completed_at.replace(tzinfo=UTC) if completed_at.tzinfo is None else completed_at
    return completed_at >= datetime.now(UTC) - timedelta(minutes=1)


def _materialize_assigned_bulk_stops(db: Session, collector: User) -> bool:
    """Materialize every outstanding bulk assignment for a collector."""
    requests = db.scalars(
        select(BulkPickupRequest)
        .where(
            BulkPickupRequest.assigned_collector_id == collector.id,
            BulkPickupRequest.status == BulkRequestStatus.ASSIGNED,
        )
        .options(joinedload(BulkPickupRequest.requester))
        .order_by(BulkPickupRequest.requested_date, BulkPickupRequest.created_at)
    ).all()
    changed = False
    for request in requests:
        ref_code = f"COL-{request.ref_code}"
        pickup = db.scalar(select(Pickup).where(Pickup.ref_code == ref_code))
        if pickup and db.scalar(
            select(DailyPickupStop.id)
            .join(DailyPickupStop.schedule)
            .where(
                DailyPickupStop.pickup_id == pickup.id,
                DailyPickupSchedule.collector_id == collector.id,
                DailyPickupSchedule.schedule_date == request.requested_date,
                DailyPickupSchedule.is_active.is_(True),
            )
        ):
            continue
        if not pickup:
            pickup = Pickup(
                ref_code=ref_code,
                citizen_id=request.requester_id,
                collector_id=collector.id,
                zone_id=request.zone_id,
                category=request.category,
                estimated_weight=request.estimated_weight or 0,
                status=PickupStatus.ASSIGNED,
                scheduled_date=request.requested_date,
                time_slot=request.time_slot,
                notes=request.notes,
            )
            db.add(pickup)
            db.flush()
        else:
            pickup.collector_id = collector.id
            pickup.status = PickupStatus.ASSIGNED
            pickup.scheduled_date = request.requested_date
            pickup.time_slot = request.time_slot
            pickup.notes = request.notes
        schedule = db.scalar(
            select(DailyPickupSchedule).where(
                DailyPickupSchedule.collector_id == collector.id,
                DailyPickupSchedule.zone_id == request.zone_id,
                DailyPickupSchedule.schedule_date == request.requested_date,
                DailyPickupSchedule.is_active.is_(True),
            )
        )
        if not schedule:
            schedule = DailyPickupSchedule(
                collector_id=collector.id,
                zone_id=request.zone_id,
                schedule_date=request.requested_date,
            )
            db.add(schedule)
            db.flush()
        schedule.total_stops += 1
        db.add(
            DailyPickupStop(
                pickup_id=pickup.id,
                schedule_id=schedule.id,
                citizen_id=request.requester_id,
                pickup_order=schedule.total_stops,
                status=PickupStopStatus.PENDING,
                latitude=request.requester.latitude,
                longitude=request.requester.longitude,
                notes=request.notes,
            )
        )
        changed = True
    return changed


@collector_router.get("/route", response_model=CollectorRouteResponse)
def get_collector_route(
    current_user: User = Depends(require_collector), db: Session = Depends(get_db)
) -> CollectorRouteResponse:
    if _materialize_assigned_bulk_stops(db, current_user):
        # Request sessions disable autoflush. Persist newly created route stops
        # before querying the route so assignments remain visible on reload.
        db.commit()
    today_start, _ = _day_bounds()
    stops = (
        db.scalars(
            select(DailyPickupStop)
            .join(DailyPickupStop.schedule)
            .where(
                DailyPickupSchedule.collector_id == current_user.id,
                DailyPickupSchedule.is_active.is_(True),
                or_(
                    DailyPickupSchedule.schedule_date >= today_start,
                    DailyPickupStop.status != PickupStopStatus.COLLECTED,
                ),
            )
            .options(
                joinedload(DailyPickupStop.pickup),
                joinedload(DailyPickupStop.citizen),
                joinedload(DailyPickupStop.schedule).joinedload(DailyPickupSchedule.zone),
                joinedload(DailyPickupStop.mixed_waste_tags),
            )
            .order_by(
                case((DailyPickupStop.status == PickupStopStatus.COLLECTED, 1), else_=0),
                DailyPickupSchedule.schedule_date,
                DailyPickupStop.pickup_order,
            )
        )
        .unique()
        .all()
    )
    # Separate pending and completed stops
    pending_stops = [s for s in stops if s.status != PickupStopStatus.COLLECTED]
    completed_stops = [s for s in stops if s.status == PickupStopStatus.COLLECTED]

    # Find starting location (collector coords or first pending with coordinates)
    start_coords = None
    if current_user.latitude is not None and current_user.longitude is not None:
        start_coords = (current_user.latitude, current_user.longitude)

    pending_with_coords = [s for s in pending_stops if s.latitude is not None and s.longitude is not None]
    pending_no_coords = [s for s in pending_stops if s.latitude is None or s.longitude is None]

    if start_coords is None and pending_with_coords:
        start_coords = (pending_with_coords[0].latitude, pending_with_coords[0].longitude)

    route_geometry = None
    optimized_pending = list(pending_stops)

    if start_coords is not None and pending_with_coords:
        settings = get_settings()
        api_key = settings.ORS_API_KEY
        
        ors_success = False
        if api_key:
            client = ORSClient(api_key=api_key)
            try:
                stop_coords = [(s.latitude, s.longitude) for s in pending_with_coords]
                res = client.optimize_route(start_coords, stop_coords)
                optimized_indices = res["optimized_indices"]
                route_geometry = res["geometry"]
                
                # Reorder pending_with_coords based on optimization result
                sorted_coords_stops = [pending_with_coords[i] for i in optimized_indices]
                
                # If some stops are unassigned or missed by ORS, append them
                visited_ids = {s.id for s in sorted_coords_stops}
                for s in pending_with_coords:
                    if s.id not in visited_ids:
                        sorted_coords_stops.append(s)
                
                pending_with_coords = sorted_coords_stops
                ors_success = True
            except Exception as e:
                logging.getLogger(__name__).warning(f"ORS route optimization failed, falling back: {e}")

        # Fallback to Nearest Neighbor if ORS was not run or failed
        if not ors_success:
            unvisited = list(pending_with_coords)
            sorted_stops = []
            current = start_coords
            geometry_coords = [list(start_coords)]
            
            while unvisited:
                nearest_stop = None
                min_dist = float("inf")
                for s in unvisited:
                    dist = (s.latitude - current[0])**2 + (s.longitude - current[1])**2
                    if dist < min_dist:
                        min_dist = dist
                        nearest_stop = s
                
                if nearest_stop is None:
                    sorted_stops.extend(unvisited)
                    break
                
                sorted_stops.append(nearest_stop)
                unvisited.remove(nearest_stop)
                current = (nearest_stop.latitude, nearest_stop.longitude)
                geometry_coords.append([nearest_stop.latitude, nearest_stop.longitude])
            
            # Return to start coords at the end of the route to complete the depot loop
            if geometry_coords and len(geometry_coords) > 1:
                geometry_coords.append(list(start_coords))
                
            pending_with_coords = sorted_stops
            route_geometry = geometry_coords

        optimized_pending = pending_with_coords + pending_no_coords
        
        # Persist updated pickup_order in the database
        order_changed = False
        for index, stop in enumerate(optimized_pending, start=1):
            if stop.pickup_order != index:
                stop.pickup_order = index
                order_changed = True
                
        for index, stop in enumerate(completed_stops, start=len(optimized_pending) + 1):
            if stop.pickup_order != index:
                stop.pickup_order = index
                order_changed = True
                
        if order_changed:
            db.commit()

        # Re-assemble stops list in the optimized/persisted order
        stops = optimized_pending + completed_stops

    zone_name = (
        f"{stops[0].schedule.zone.code} - {stops[0].schedule.zone.name}"
        if stops
        else "No assigned zone"
    )
    return CollectorRouteResponse(
        schedule_id=stops[0].schedule_id if stops else None,
        zone_name=zone_name,
        pickup_count=len(stops),
        completed_count=sum(stop.status == PickupStopStatus.COLLECTED for stop in stops),
        flagged_count=sum(bool(stop.mixed_waste_tags) for stop in stops),
        collector_latitude=current_user.latitude,
        collector_longitude=current_user.longitude,
        route_geometry=route_geometry,
        ordered_pickups=[
            _collector_stop(stop, pickup_order=index) for index, stop in enumerate(stops, start=1)
        ],
    )


@collector_router.post("/stops/{stop_id}/complete", response_model=CollectorStopResponse)
def complete_stop(
    stop_id: UUID, current_user: User = Depends(require_collector), db: Session = Depends(get_db)
) -> CollectorStopResponse:
    stop = _owned_stop(db, stop_id, current_user.id)
    _ensure_not_collected(stop)
    now = datetime.now(UTC)
    stop.status = PickupStopStatus.COLLECTED
    stop.completed_at = now
    stop.pickup.status = PickupStatus.COLLECTED
    stop.pickup.completed_at = now
    _sync_source_bulk_pickup(db, stop, BulkRequestStatus.COLLECTED, now)
    _refresh_schedule_completion(stop.schedule, db)
    db.add(
        Notification(
            user_id=stop.citizen_id,
            title="Pickup collected",
            body=f"{stop.pickup.ref_code} was collected.",
        )
    )
    pool_and_maybe_create_batches(db, stop.schedule.zone_id)
    db.commit()
    db.refresh(stop)
    return _collector_stop(stop)


@collector_router.post("/stops/{stop_id}/undo", response_model=CollectorStopResponse)
def undo_complete_stop(
    stop_id: UUID, current_user: User = Depends(require_collector), db: Session = Depends(get_db)
) -> CollectorStopResponse:
    stop = _owned_stop(db, stop_id, current_user.id)
    if stop.status != PickupStopStatus.COLLECTED or not stop.completed_at:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This pickup is not completed.",
        )
    if not _is_within_undo_window(stop.completed_at):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The one-minute undo window has expired.",
        )
    stop.status = PickupStopStatus.PENDING
    stop.completed_at = None
    stop.pickup.status = PickupStatus.ASSIGNED
    stop.pickup.completed_at = None
    _sync_source_bulk_pickup(
        db,
        stop,
        BulkRequestStatus.ASSIGNED,
        None,
        is_flagged=False,
    )
    _refresh_schedule_completion(stop.schedule, db)
    db.commit()
    db.refresh(stop)
    return _collector_stop(stop)


@collector_router.get("/completed-collections", response_model=list[CollectorStopResponse])
def list_completed_collections(
    current_user: User = Depends(require_collector), db: Session = Depends(get_db)
) -> list[CollectorStopResponse]:
    stops = (
        db.scalars(
            select(DailyPickupStop)
            .join(DailyPickupStop.schedule)
            .where(
                DailyPickupSchedule.collector_id == current_user.id,
                DailyPickupStop.status == PickupStopStatus.COLLECTED,
            )
            .options(
                joinedload(DailyPickupStop.pickup),
                joinedload(DailyPickupStop.citizen),
                joinedload(DailyPickupStop.schedule).joinedload(DailyPickupSchedule.zone),
                joinedload(DailyPickupStop.mixed_waste_tags),
            )
            .order_by(DailyPickupStop.completed_at.desc())
        )
        .unique()
        .all()
    )
    return [_collector_stop(stop) for stop in stops]


@collector_router.post("/stops/{stop_id}/notify")
def notify_citizen_of_delay(
    stop_id: UUID,
    payload: DelayStopRequest,
    current_user: User = Depends(require_collector),
    db: Session = Depends(get_db),
) -> dict:
    stop = _owned_stop(db, stop_id, current_user.id)
    _ensure_not_collected(stop)
    stop.status = PickupStopStatus.DELAYED
    db.add(
        DelayLog(
            stop_id=stop.id,
            worker_id=current_user.id,
            reason=payload.reason,
            note=payload.message.strip(),
        )
    )
    db.add(
        Notification(
            user_id=stop.citizen_id,
            title="Pickup update",
            body=payload.message.strip(),
        )
    )
    db.commit()
    return {"message": "Citizen notified."}


@collector_router.post("/stops/{stop_id}/flag")
def flag_mixed_waste(
    stop_id: UUID,
    payload: MixedWasteRequest,
    current_user: User = Depends(require_collector),
    db: Session = Depends(get_db),
) -> dict:
    stop = _owned_stop(db, stop_id, current_user.id)
    _ensure_not_collected(stop)
    now = datetime.now(UTC)
    stop.status = PickupStopStatus.COLLECTED
    stop.completed_at = now
    stop.pickup.status = PickupStatus.COLLECTED
    stop.pickup.completed_at = now
    _sync_source_bulk_pickup(
        db,
        stop,
        BulkRequestStatus.COLLECTED,
        now,
        is_flagged=True,
        flag_severity=payload.severity,
        flag_note=payload.description.strip(),
    )
    _refresh_schedule_completion(stop.schedule, db)
    db.add(
        MixedWasteTag(
            stop_id=stop.id,
            worker_id=current_user.id,
            severity=payload.severity,
            note=payload.description.strip(),
        )
    )
    db.add(
        Notification(
            user_id=stop.citizen_id,
            title="Pickup completed with a waste-quality flag",
            body=f"{stop.pickup.ref_code} was collected and needs a waste-quality review.",
        )
    )
    notify_zone_managers(
        db,
        stop.schedule.zone_id,
        "Mixed waste flagged",
        (
            f"{stop.pickup.ref_code} was flagged as {payload.severity.value.lower()} "
            f"by {current_user.name}."
        ),
    )
    pool_and_maybe_create_batches(db, stop.schedule.zone_id)
    db.commit()
    return {"message": "Flag recorded for manager review."}


@collector_router.post("/stops/{stop_id}/clean")
def mark_stop_clean(
    stop_id: UUID, current_user: User = Depends(require_collector), db: Session = Depends(get_db)
) -> dict:
    stop = _owned_stop(db, stop_id, current_user.id)
    stop.pickup.is_contaminated = False
    stop.pickup.contamination_cleared_by_id = current_user.id
    stop.pickup.contamination_cleared_at = datetime.now(UTC)
    db.commit()
    return {"message": "Pickup marked clean."}


@collector_router.get("/notifications")
def list_collector_notifications(
    current_user: User = Depends(require_collector), db: Session = Depends(get_db)
) -> list:
    return list_for_user(db, current_user.id)


@collector_router.patch("/notifications/{notification_id}/read")
def mark_collector_notification_read(
    notification_id: UUID,
    current_user: User = Depends(require_collector),
    db: Session = Depends(get_db),
) -> dict:
    notification = mark_read(db, notification_id, current_user.id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return notification.model_dump()


@collector_router.patch("/notifications/read")
def mark_all_collector_notifications_read(
    current_user: User = Depends(require_collector), db: Session = Depends(get_db)
) -> dict:
    result = db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
    return {"marked_read": result.rowcount}
