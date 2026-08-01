from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.features.bulk_pickups.models import BulkPickupRequest
from app.features.collection_ops.models import (
    DailyPickupSchedule,
    DailyPickupStop,
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
from app.features.notifications.models import Notification
from app.features.notifications.service import list_for_user, mark_read
from app.features.users.dependencies import require_collector, require_resident
from app.features.users.models import User
from app.models.enums import BulkRequestStatus, PickupStatus, PickupStopStatus

router = APIRouter(tags=["Resident Collection Schedules"])
collector_router = APIRouter(prefix="/collector", tags=["Collector Operations"])


@router.get("/daily-pickup-schedules", response_model=list[DailyPickupScheduleResponse])
def list_daily_pickup_schedules(
    current_user: User = Depends(require_resident), db: Session = Depends(get_db)
) -> list[DailyPickupScheduleResponse]:
    stops = (
        db.scalars(
            select(DailyPickupStop)
            .where(DailyPickupStop.resident_id == current_user.id)
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
    stop: DailyPickupStop, pickup_order: int | None = None, is_flagged: bool = False
) -> CollectorStopResponse:
    return CollectorStopResponse(
        id=stop.id,
        ref_code=stop.pickup.ref_code,
        status=stop.status.value,
        pickup_order=pickup_order if pickup_order is not None else stop.pickup_order,
        resident_name=stop.resident.name,
        category=stop.pickup.category,
        estimated_weight=float(stop.pickup.estimated_weight),
        pickup_address=stop.notes,
        zone_name=stop.schedule.zone.name,
        time_slot=stop.pickup.time_slot,
        pickup_latitude=stop.latitude,
        pickup_longitude=stop.longitude,
        completed_at=stop.completed_at,
        is_flagged=is_flagged,
    )


def _bulk_pickup_response(
    pickup: BulkPickupRequest, pickup_order: int, is_flagged: bool | None = None
) -> CollectorStopResponse:
    return CollectorStopResponse(
        id=pickup.id,
        ref_code=pickup.ref_code,
        status=pickup.status.value,
        pickup_order=pickup_order,
        resident_name=pickup.requester.name,
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
            joinedload(DailyPickupStop.resident),
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


def _is_within_undo_window(completed_at: datetime | None) -> bool:
    if not completed_at:
        return False
    # SQLite test databases may round-trip timezone-aware datetimes as naive.
    completed_at = completed_at.replace(tzinfo=UTC) if completed_at.tzinfo is None else completed_at
    return completed_at >= datetime.now(UTC) - timedelta(minutes=1)


def _materialize_assigned_bulk_stops(db: Session, collector: User) -> bool:
    """Make assignments created before route integration visible to collectors."""
    requests = db.scalars(
        select(BulkPickupRequest)
        .where(
            BulkPickupRequest.assigned_collector_id == collector.id,
            BulkPickupRequest.status == BulkRequestStatus.ASSIGNED,
        )
        .options(joinedload(BulkPickupRequest.requester))
    ).all()
    changed = False
    for request in requests:
        ref_code = f"COL-{request.ref_code}"
        if db.scalar(select(Pickup.id).where(Pickup.ref_code == ref_code)):
            continue
        pickup = Pickup(
            ref_code=ref_code,
            resident_id=request.requester_id,
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
                resident_id=request.requester_id,
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
    pickups = (
        db.scalars(
            select(BulkPickupRequest)
            .where(BulkPickupRequest.assigned_collector_id == current_user.id)
            .options(joinedload(BulkPickupRequest.requester), joinedload(BulkPickupRequest.zone))
            .order_by(BulkPickupRequest.requested_date, BulkPickupRequest.created_at)
        )
        .unique()
        .all()
    )
    outstanding = [pickup for pickup in pickups if pickup.status != BulkRequestStatus.COLLECTED]
    collected = [pickup for pickup in pickups if pickup.status == BulkRequestStatus.COLLECTED]
    pickups = outstanding + collected
    zone_name = (
        f"{pickups[0].zone.code} - {pickups[0].zone.name}" if pickups else "No assigned zone"
    )
    return CollectorRouteResponse(
        zone_name=zone_name,
        pickup_count=len(pickups),
        completed_count=sum(pickup.status == BulkRequestStatus.COLLECTED for pickup in pickups),
        flagged_count=sum(pickup.is_flagged for pickup in pickups),
        collector_latitude=current_user.latitude,
        collector_longitude=current_user.longitude,
        ordered_pickups=[
            _bulk_pickup_response(
                pickup,
                (
                    outstanding.index(pickup) + 1
                    if pickup.status != BulkRequestStatus.COLLECTED
                    else 0
                ),
            )
            for pickup in pickups
        ],
    )


@collector_router.post("/stops/{stop_id}/complete", response_model=CollectorStopResponse)
def complete_stop(
    stop_id: UUID, current_user: User = Depends(require_collector), db: Session = Depends(get_db)
) -> CollectorStopResponse:
    pickup = _owned_bulk_pickup(db, stop_id, current_user.id)
    now = datetime.now(UTC)
    pickup.status = BulkRequestStatus.COLLECTED
    pickup.collected_at = now
    db.add(
        Notification(
            user_id=pickup.requester_id,
            title="Pickup collected",
            body=f"{pickup.ref_code} was collected.",
        )
    )
    db.commit()
    db.refresh(pickup)
    return _bulk_pickup_response(pickup, 0)


@collector_router.post("/stops/{stop_id}/undo", response_model=CollectorStopResponse)
def undo_complete_stop(
    stop_id: UUID, current_user: User = Depends(require_collector), db: Session = Depends(get_db)
) -> CollectorStopResponse:
    pickup = _owned_bulk_pickup(db, stop_id, current_user.id)
    if pickup.status != BulkRequestStatus.COLLECTED or not pickup.collected_at:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This pickup is not completed.",
        )
    if not _is_within_undo_window(pickup.collected_at):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The one-minute undo window has expired.",
        )
    pickup.status = BulkRequestStatus.ASSIGNED
    pickup.collected_at = None
    pickup.is_flagged = False
    pickup.flag_severity = None
    pickup.flag_note = None
    db.commit()
    db.refresh(pickup)
    return _bulk_pickup_response(pickup, 0)


@collector_router.get("/completed-collections", response_model=list[CollectorStopResponse])
def list_completed_collections(
    current_user: User = Depends(require_collector), db: Session = Depends(get_db)
) -> list[CollectorStopResponse]:
    pickups = (
        db.scalars(
            select(BulkPickupRequest)
            .where(
                BulkPickupRequest.assigned_collector_id == current_user.id,
                BulkPickupRequest.status == BulkRequestStatus.COLLECTED,
            )
            .options(joinedload(BulkPickupRequest.requester), joinedload(BulkPickupRequest.zone))
            .order_by(BulkPickupRequest.collected_at.desc())
        )
        .unique()
        .all()
    )
    return [_bulk_pickup_response(pickup, index) for index, pickup in enumerate(pickups, start=1)]


@collector_router.post("/stops/{stop_id}/notify")
def notify_resident_of_delay(
    stop_id: UUID,
    payload: DelayStopRequest,
    current_user: User = Depends(require_collector),
    db: Session = Depends(get_db),
) -> dict:
    pickup = _owned_bulk_pickup(db, stop_id, current_user.id)
    db.add(
        Notification(
            user_id=pickup.requester_id,
            title="Pickup update",
            body=payload.message.strip(),
        )
    )
    db.commit()
    return {"message": "Resident notified."}


@collector_router.post("/stops/{stop_id}/flag")
def flag_mixed_waste(
    stop_id: UUID,
    payload: MixedWasteRequest,
    current_user: User = Depends(require_collector),
    db: Session = Depends(get_db),
) -> dict:
    pickup = _owned_bulk_pickup(db, stop_id, current_user.id)
    now = datetime.now(UTC)
    pickup.status = BulkRequestStatus.COLLECTED
    pickup.collected_at = now
    pickup.is_flagged = True
    pickup.flag_severity = payload.severity
    pickup.flag_note = payload.description.strip()
    db.add(
        Notification(
            user_id=pickup.requester_id,
            title="Pickup completed with a waste-quality flag",
            body=f"{pickup.ref_code} was collected and needs a waste-quality review.",
        )
    )
    notify_zone_managers(
        db,
        pickup.zone_id,
        "Mixed waste flagged",
        (
            f"{pickup.ref_code} was flagged as {payload.severity.value.lower()} "
            f"by {current_user.name}."
        ),
    )
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
