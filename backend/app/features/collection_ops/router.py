from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.features.collection_ops.models import DailyPickupSchedule, DailyPickupStop
from app.features.collection_ops.schemas import DailyPickupScheduleResponse
from app.features.users.dependencies import require_resident
from app.features.users.models import User

router = APIRouter(tags=["Resident Collection Schedules"])


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
