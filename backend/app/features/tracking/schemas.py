from datetime import datetime

from pydantic import BaseModel


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
