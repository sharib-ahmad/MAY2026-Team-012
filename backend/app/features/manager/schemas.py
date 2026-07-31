import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------


class WardSummary(BaseModel):
    """Per-ward roll-up shown in the manager overview table."""

    id: uuid.UUID
    code: str
    name: str
    residents_count: int
    routes_today: int
    routes_completed_today: int
    active_workers: int
    coverage_pct: int

    model_config = ConfigDict(from_attributes=True)


class ComplaintTrendPoint(BaseModel):
    """Complaints filed vs. resolved for a single day, used in the weekly chart."""

    day: str
    filed: int
    resolved: int


class OverviewStats(BaseModel):
    """Headline stats shown on the manager overview hero band."""

    open_complaints: int
    needs_attention_complaints: int
    resolved_this_week: int
    avg_resolution_hours: float
    routes_today: int
    routes_completed_today: int
    route_points_total: int
    route_points_collected: int
    active_workers: int
    wards_supervised: int


class ManagerOverviewResponse(BaseModel):
    """Everything the manager Overview tab needs in a single call."""

    stats: OverviewStats
    wards: list[WardSummary]
    complaints_trend: list[ComplaintTrendPoint]
    needs_attention: list["ComplaintOut"]
    mixed_waste_flags: list["MixedWasteFlagOut"]


# ---------------------------------------------------------------------------
# Complaints
# ---------------------------------------------------------------------------


class ComplaintOut(BaseModel):
    id: uuid.UUID
    ref_code: str
    zone_id: uuid.UUID | None = None
    zone_code: str | None = None
    zone_name: str | None = None
    citizen_name: str
    issue_type: str
    status: str
    description: str
    created_at: datetime
    resolved_at: datetime | None = None
    resolved_by_name: str | None = None
    resolution_notes: str | None = None
    is_aging: bool

    model_config = ConfigDict(from_attributes=True)


class ComplaintListResponse(BaseModel):
    complaints: list[ComplaintOut]
    total: int


class ComplaintUpdate(BaseModel):
    """Manager update to move a ticket forward or close it out."""

    status: str = Field(..., description="One of IN_PROGRESS, RESOLVED, REOPENED, CLOSED")
    resolution_notes: str | None = Field(None, max_length=2000)


# ---------------------------------------------------------------------------
# Route tracking
# ---------------------------------------------------------------------------


class RouteStopOut(BaseModel):
    id: uuid.UUID
    seq: int
    label: str
    status: str
    updated_at: datetime | None = None


class DelayLogOut(BaseModel):
    id: uuid.UUID
    route_id: uuid.UUID
    zone_code: str | None = None
    worker_name: str
    reason: str
    note: str | None = None
    logged_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MixedWasteFlagOut(BaseModel):
    id: uuid.UUID
    route_id: uuid.UUID
    zone_code: str | None = None
    point_label: str
    severity: str
    note: str | None = None
    flagged_at: datetime
    worker_name: str

    model_config = ConfigDict(from_attributes=True)


class RouteOut(BaseModel):
    id: uuid.UUID
    zone_id: uuid.UUID
    zone_code: str | None = None
    zone_name: str | None = None
    worker_id: uuid.UUID
    worker_name: str
    schedule_date: datetime
    status: str
    points_total: int
    points_collected: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_update_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class RouteDetailOut(RouteOut):
    points: list[RouteStopOut]


class RouteListResponse(BaseModel):
    routes: list[RouteOut]
    total: int
    delay_logs: list[DelayLogOut]
    mixed_waste_flags: list[MixedWasteFlagOut]


# ---------------------------------------------------------------------------
# Crews
# ---------------------------------------------------------------------------


class WorkerOut(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    zone_id: uuid.UUID | None = None
    zone_code: str | None = None
    availability: str | None = None
    status: str
    active_route_id: uuid.UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class WorkerListResponse(BaseModel):
    workers: list[WorkerOut]
    total: int


class WorkerReassignRequest(BaseModel):
    """Move a worker to another ward and/or availability state."""

    zone_id: uuid.UUID | None = None
    availability: str | None = Field(
        None, description="One of AVAILABLE, UNAVAILABLE, ON_ROUTE"
    )


ManagerOverviewResponse.model_rebuild()