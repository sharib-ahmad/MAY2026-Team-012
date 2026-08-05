"""Notification query and update helpers."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.notifications.models import Notification
from app.features.notifications.schemas import NotificationResponse


def serialize_notification(notification: Notification) -> NotificationResponse:
    return NotificationResponse(
        id=notification.id,
        title=notification.title,
        body=notification.body,
        is_read=notification.is_read,
        created_at=notification.created_at,
    )


def list_for_user(db: Session, user_id: uuid.UUID, limit: int = 20) -> list[NotificationResponse]:
    notifications = db.scalars(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    ).all()
    return [serialize_notification(notification) for notification in notifications]


def mark_read(
    db: Session, notification_id: uuid.UUID, user_id: uuid.UUID
) -> NotificationResponse | None:
    notification = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    if not notification:
        return None
    notification.is_read = True
    db.commit()
    return serialize_notification(notification)


def mark_all_read(db: Session, user_id: uuid.UUID) -> None:
    notifications = db.scalars(
        select(Notification).where(Notification.user_id == user_id, not Notification.is_read)
    ).all()
    for n in notifications:
        n.is_read = True
    db.commit()
