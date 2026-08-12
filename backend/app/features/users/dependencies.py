from fastapi import Depends, HTTPException, status

from app.features.auth.dependencies import get_current_user
from app.features.users.models import User
from app.models.enums import Role


def require_citizen(current_user: User = Depends(get_current_user)) -> User:
    """Require the authenticated user to be a citizen/citizen."""
    if current_user.role != Role.CITIZEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Citizen access required.",
        )
    return current_user


def require_collector(current_user: User = Depends(get_current_user)) -> User:
    """Require the authenticated user to be a collection worker."""
    if current_user.role != Role.COLLECTION_WORKER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Collector access required.",
        )
    return current_user


def require_recycler(current_user: User = Depends(get_current_user)) -> User:
    """Require the authenticated user to be a recycler."""
    if current_user.role != Role.RECYCLER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recycler access required.",
        )
    return current_user
