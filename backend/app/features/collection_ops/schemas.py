import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import DelayReason, WasteSeverity


class DailyPickupScheduleResponse(BaseModel):
    schedule_id: uuid.UUID
    schedule_date: datetime
    collector_name: str | None = None
    pickup_order: int
    stop_status: str
    total_stops: int
    completed_stops: int


class CollectorStopResponse(BaseModel):
    id: uuid.UUID
    ref_code: str
    status: str
    pickup_order: int
    resident_name: str
    category: str
    estimated_weight: float
    pickup_address: str | None = None
    zone_name: str
    time_slot: str | None = None
    pickup_latitude: float | None = None
    pickup_longitude: float | None = None
    completed_at: datetime | None = None
    is_flagged: bool = False


class CollectorRouteResponse(BaseModel):
    schedule_id: uuid.UUID | None = None
    zone_name: str
    pickup_count: int
    completed_count: int
    flagged_count: int
    collector_latitude: float | None = None
    collector_longitude: float | None = None
    ordered_pickups: list[CollectorStopResponse]


class DelayStopRequest(BaseModel):
    reason: DelayReason
    message: str = Field(min_length=5, max_length=200)


class MixedWasteRequest(BaseModel):
    severity: WasteSeverity
    description: str = Field(min_length=10, max_length=300)
