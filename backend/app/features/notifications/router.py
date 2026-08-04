import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.notifications.schemas import NotificationResponse
from app.features.notifications.service import list_for_user, mark_read
from app.features.users.dependencies import require_citizen
from app.features.users.models import User

router = APIRouter(tags=["Citizen Notifications"])


@router.get("/notifications", response_model=list[NotificationResponse])
def list_notifications(
    current_user: User = Depends(require_citizen), db: Session = Depends(get_db)
) -> list[NotificationResponse]:
    return list_for_user(db, current_user.id)


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(require_citizen),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    notification = mark_read(db, notification_id, current_user.id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return notification
