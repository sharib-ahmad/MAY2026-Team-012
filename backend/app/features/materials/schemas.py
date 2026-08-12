"""Batch assignment API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class RecyclerOption(BaseModel):
    id: uuid.UUID
    name: str
    email: str


class BatchSummary(BaseModel):
    id: uuid.UUID
    ref_code: str
    status: str
    waste_category: str
    declared_weight: float
    final_weight: float | None = None
    quality_status: str
    contamination_note: str | None = None
    rejection_reason: str | None = None
    remarks: str | None = None
    zone_id: uuid.UUID | None = None
    zone_code: str | None = None
    zone_name: str | None = None
    destination_recycler_id: uuid.UUID | None = None
    destination_recycler_name: str | None = None
    pickup_count: int
    pickup_ref_codes: list[str]
    collected_at: datetime | None = None
    assigned_at: datetime | None = None
    rejected_at: datetime | None = None
    processed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AssignBatchRequest(BaseModel):
    recycler_id: uuid.UUID


class RejectBatchRequest(BaseModel):
    note: str = Field(min_length=1, max_length=500)

    @field_validator("note")
    @classmethod
    def strip_and_require_note(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Note must not be blank.")
        return stripped
