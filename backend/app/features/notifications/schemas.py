"""Notification API response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: uuid.UUID
    title: str
    body: str
    is_read: bool
    created_at: datetime
