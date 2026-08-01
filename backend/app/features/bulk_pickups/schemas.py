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
