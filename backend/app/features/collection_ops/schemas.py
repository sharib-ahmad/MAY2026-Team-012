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
    citizen_name: str
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
    depot_latitude: float | None = None
    depot_longitude: float | None = None
    route_geometry: list[list[float]] | None = None
    ordered_pickups: list[CollectorStopResponse]
    total_distance_km: float = 0.0
    estimated_duration_min: float = 0.0
    is_degraded: bool = False
    degraded_notice: str | None = None


class DelayStopRequest(BaseModel):
    reason: DelayReason
    message: str = Field(min_length=5, max_length=200)


class MixedWasteRequest(BaseModel):
    severity: WasteSeverity
    description: str = Field(min_length=10, max_length=300)


class PublicTrackingEvent(BaseModel):
    stage: str
    label: str
    at: datetime


class PublicTrackingResponse(BaseModel):
    ref_code: str
    entity_type: str
    status: str
    category: str | None = None
    issue_type: str | None = None
    scheduled_date: datetime | None = None
    created_at: datetime
    last_updated: datetime
    timeline: list[PublicTrackingEvent]
    citizen_name: str | None = None
    zone_name: str | None = None
    manager_name: str | None = None
    collector_name: str | None = None
    recycler_name: str | None = None
