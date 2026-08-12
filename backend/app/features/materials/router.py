"""Manager and recycler batch assignment endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.manager.dependencies import require_manager
from app.features.materials.schemas import AssignBatchRequest, BatchSummary, RejectBatchRequest
from app.features.materials.service import (
    accept_batch,
    assign_batch,
    list_manager_batches,
    list_recycler_batches,
    list_recyclers,
    process_batch,
    reject_batch,
)
from app.features.notifications.models import Notification
from app.features.notifications.service import list_for_user, mark_read
from app.features.users.dependencies import require_recycler
from app.features.users.models import User
from app.models.enums import BatchStatus

manager_router = APIRouter(prefix="/manager", tags=["Manager Batches"])
recycler_router = APIRouter(prefix="/recycler", tags=["Recycler Batches"])


@manager_router.get("/batches", response_model=list[BatchSummary])
def get_manager_batches(
    current_user: User = Depends(require_manager), db: Session = Depends(get_db)
) -> list[BatchSummary]:
    return list_manager_batches(db, current_user)


@manager_router.get("/recyclers")
def get_manager_recyclers(
    current_user: User = Depends(require_manager), db: Session = Depends(get_db)
) -> list[dict]:
    del current_user
    return list_recyclers(db)


@manager_router.post("/batches/{batch_id}/assign", response_model=BatchSummary)
def assign_manager_batch(
    batch_id: UUID,
    payload: AssignBatchRequest,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> BatchSummary:
    return assign_batch(db, current_user, batch_id, payload.recycler_id)


@recycler_router.get("/batches", response_model=list[BatchSummary])
def get_recycler_batches(
    current_user: User = Depends(require_recycler), db: Session = Depends(get_db)
) -> list[BatchSummary]:
    return list_recycler_batches(
        db,
        current_user,
        {BatchStatus.ASSIGNED, BatchStatus.PROCESSING, BatchStatus.PROCESSED},
    )


@recycler_router.post("/batches/{batch_id}/accept", response_model=BatchSummary)
def accept_recycler_batch(
    batch_id: UUID,
    current_user: User = Depends(require_recycler),
    db: Session = Depends(get_db),
) -> BatchSummary:
    return accept_batch(db, current_user, batch_id)


@recycler_router.post("/batches/{batch_id}/reject", response_model=BatchSummary)
def reject_recycler_batch(
    batch_id: UUID,
    payload: RejectBatchRequest,
    current_user: User = Depends(require_recycler),
    db: Session = Depends(get_db),
) -> BatchSummary:
    return reject_batch(db, current_user, batch_id, payload.note)


@recycler_router.post("/batches/{batch_id}/process", response_model=BatchSummary)
def process_recycler_batch(
    batch_id: UUID,
    current_user: User = Depends(require_recycler),
    db: Session = Depends(get_db),
) -> BatchSummary:
    return process_batch(db, current_user, batch_id)


@recycler_router.get("/notifications")
def list_recycler_notifications(
    current_user: User = Depends(require_recycler), db: Session = Depends(get_db)
) -> list:
    return list_for_user(db, current_user.id)


@recycler_router.patch("/notifications/{notification_id}/read")
def mark_recycler_notification_read(
    notification_id: UUID,
    current_user: User = Depends(require_recycler),
    db: Session = Depends(get_db),
) -> dict:
    notification = mark_read(db, notification_id, current_user.id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return notification.model_dump()


@recycler_router.patch("/notifications/read")
def mark_all_recycler_notifications_read(
    current_user: User = Depends(require_recycler), db: Session = Depends(get_db)
) -> dict:
    result = db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .values(is_read=True)
    )
    db.commit()
    return {"marked_read": result.rowcount}
