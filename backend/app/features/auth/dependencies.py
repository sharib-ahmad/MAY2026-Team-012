import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.features.users.models import User
from app.models.enums import Role, UserStatus

security_bearer = HTTPBearer(auto_error=True)

# The public API exposes the canonical database role names.
ROLE_MAP_DB_TO_FRONTEND = {
    Role.CITIZEN: "CITIZEN",
    Role.COLLECTION_WORKER: "COLLECTION_WORKER",
    Role.RECYCLER: "RECYCLER",
    Role.MUNICIPAL_OFFICER: "MUNICIPAL_OFFICER",
    Role.SYSTEM_ADMIN: "SYSTEM_ADMIN",
}


def get_current_user(
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(security_bearer),
) -> User:
    """FastAPI dependency to extract and authenticate the current user using JWT."""
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: str | None = payload.get("sub")
        token_version: int | None = payload.get("token_version")
        if user_id is None:
            raise credentials_exception
    except JWTError as err:
        raise credentials_exception from err

    # Query user from database
    user = db.scalar(
        select(User).where(
            User.id == uuid.UUID(user_id),
            User.deleted_at.is_(None),
        )
    )
    if user is None:
        raise credentials_exception

    # Check status
    if user.status == UserStatus.DISABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been suspended by an administrator.",
        )

    # Check token version
    if token_version is not None and token_version != user.token_version:
        raise credentials_exception

    return user
