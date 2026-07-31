import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.auth.dependencies import get_current_user
from app.features.users.models import User
from app.models.enums import Role
from app.models.zone import Zone


def require_manager(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure the current user is a municipal officer (manager).

    System admins are also allowed through so they can supervise/oversee any
    ward from the same endpoints, mirroring how the admin portal can act on
    manager-owned resources elsewhere in the API.
    """
    if current_user.role not in (Role.MUNICIPAL_OFFICER, Role.SYSTEM_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires manager privileges.",
        )
    return current_user


def get_manager_zone_ids(current_user: User, db: Session) -> list[uuid.UUID] | None:
    """Return the zone IDs a manager is scoped to, or None for unrestricted access.

    A manager is scoped to the wards they are the assigned manager of
    (``Zone.manager_id``), falling back to their own ``zone_id`` when no ward
    has been assigned to them yet. System admins are unrestricted (None).
    """
    if current_user.role == Role.SYSTEM_ADMIN:
        return None

    managed = db.scalars(select(Zone.id).where(Zone.manager_id == current_user.id)).all()
    if managed:
        return list(managed)

    if current_user.zone_id:
        return [current_user.zone_id]

    return []
