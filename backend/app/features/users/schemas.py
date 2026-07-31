import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PickupCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=20)
    estimated_weight: float = Field(..., gt=0, le=1000)
    scheduled_date: datetime
    time_slot: Literal["Morning (8-11)", "Midday (11-2)", "Evening (4-7)"]
    notes: str | None = Field(default=None, max_length=500)


class PickupResponse(BaseModel):
    id: uuid.UUID
    ref_code: str
    category: str
    estimated_weight: float
    actual_weight: float | None = None
    scheduled_date: datetime | None = None
    time_slot: str | None = None
    notes: str | None = None
    status: str
    zone_name: str | None = None
    collector_name: str | None = None
    collector_phone: str | None = None
    created_at: datetime


class PickupsResponse(BaseModel):
    pickups: list[PickupResponse]
    total: int


class ImpactCategory(BaseModel):
    category: str
    weight_kg: float
    credits: float
    co2_kg: float


class ImpactMonth(BaseModel):
    month: str
    weight_kg: float


class ImpactBadge(BaseModel):
    code: str
    name: str
    icon: str
    earned: bool


class ImpactResponse(BaseModel):
    total_pickups: int
    total_kg_diverted: float
    co2_saved_kg: float
    credits_balance: float
    by_category: list[ImpactCategory]
    monthly_trend: list[ImpactMonth]
    badges: list[ImpactBadge]


class TrackingEvent(BaseModel):
    stage: str
    label: str
    at: datetime


class PickupTrackingResponse(BaseModel):
    ref_code: str
    status: str
    stops_remaining: int
    estimated_arrival: str | None = None
    timeline: list[TrackingEvent]


class TicketCreate(BaseModel):
    issue_type: Literal["MISSED_PICKUP", "OVERFLOW", "MIXED_WASTE", "DELAY", "OTHER"]
    description: str = Field(..., min_length=10, max_length=500)


class TicketResponse(BaseModel):
    id: uuid.UUID
    ref_code: str
    issue_type: str
    status: str
    description: str
    ward_code: str | None = None
    ward_name: str | None = None
    ward_sectors: str | None = None
    ward_manager_name: str | None = None
    created_at: datetime


class TicketsResponse(BaseModel):
    tickets: list[TicketResponse]
    total: int


class DailyPickupScheduleResponse(BaseModel):
    schedule_id: uuid.UUID
    schedule_date: datetime
    collector_name: str | None = None
    pickup_order: int
    stop_status: str
    total_stops: int
    completed_stops: int


class NotificationResponse(BaseModel):
    id: uuid.UUID
    title: str
    body: str
    is_read: bool
    created_at: datetime
