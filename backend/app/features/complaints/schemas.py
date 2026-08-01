import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    issue_type: Literal["MISSED_PICKUP", "OVERFLOW", "MIXED_WASTE", "DELAY", "OTHER"]
    description: str = Field(..., min_length=10, max_length=500)


class TicketResponse(BaseModel):
    id: uuid.UUID
    ref_code: str
    issue_type: str
    status: str
    description: str
    manager_note: str | None = None
    ward_code: str | None = None
    ward_name: str | None = None
    ward_sectors: str | None = None
    ward_manager_name: str | None = None
    created_at: datetime


class TicketsResponse(BaseModel):
    tickets: list[TicketResponse]
    total: int
