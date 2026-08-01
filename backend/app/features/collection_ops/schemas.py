import uuid
from datetime import datetime

from pydantic import BaseModel


class DailyPickupScheduleResponse(BaseModel):
    schedule_id: uuid.UUID
    schedule_date: datetime
    collector_name: str | None = None
    pickup_order: int
    stop_status: str
    total_stops: int
    completed_stops: int
