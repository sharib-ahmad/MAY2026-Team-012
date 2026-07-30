from fastapi import Depends, HTTPException, status

from app.features.auth.dependencies import get_current_user
from app.features.users.models import User
from app.models.enums import Role


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure the current user is a system admin."""
    if current_user.role != Role.SYSTEM_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires admin privileges.",
        )
    return current_user
