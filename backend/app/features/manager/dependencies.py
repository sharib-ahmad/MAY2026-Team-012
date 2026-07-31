from fastapi import Depends, HTTPException, status

from app.features.auth.dependencies import get_current_user
from app.features.users.models import User
from app.models.enums import Role


def require_manager(current_user: User = Depends(get_current_user)) -> User:
    """Allow access only to municipal officers."""
    if current_user.role != Role.MUNICIPAL_OFFICER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Manager access required."
        )
    return current_user
