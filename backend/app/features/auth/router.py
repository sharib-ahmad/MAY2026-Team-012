from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.features.auth.dependencies import (
    ROLE_MAP_DB_TO_FRONTEND,
    get_current_user,
)
from app.features.auth.schemas import (
    AuthenticatedUser,
    LoginRequest,
    TokenResponse,
    UserRegisterRequest,
)
from app.features.users.models import User
from app.models.enums import Role, UserStatus
from app.models.zone import Zone

router = APIRouter(tags=["Authentication"])

# Map frontend roles to database Role enums
ROLE_MAP_FRONTEND_TO_DB = {
    "RESIDENT": Role.CITIZEN,
    "COLLECTOR": Role.COLLECTION_WORKER,
    "RECYCLER": Role.RECYCLER,
    "MANAGER": Role.MUNICIPAL_OFFICER,
    "ADMIN": Role.SYSTEM_ADMIN,
}


@router.post("/register", response_model=TokenResponse)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)) -> Any:
    """Register a new user account on the platform."""
    # Check if email is already registered
    existing_user_email = db.scalar(select(User).where(User.email == request.email.lower()))
    if existing_user_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Check if phone is already registered
    existing_user_phone = db.scalar(select(User).where(User.phone == request.phone))
    if existing_user_phone:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this phone number already exists.",
        )

    # Resolve database Role enum from registration input
    frontend_role = request.role.upper()
    db_role = ROLE_MAP_FRONTEND_TO_DB.get(frontend_role)
    if not db_role:
        # Fallback if already database name
        try:
            db_role = Role[frontend_role]
        except KeyError as err:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported role: {request.role}",
            ) from err

    # If zone_id is provided, verify it exists
    if request.zone_id:
        zone = db.scalar(select(Zone).where(Zone.id == request.zone_id))
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Selected ward does not exist.",
            )

    # Hash the password and create the user
    hashed_password = get_password_hash(request.password)
    user = User(
        name=request.name,
        email=request.email.lower(),
        password_hash=hashed_password,
        phone=request.phone,
        role=db_role,
        zone_id=request.zone_id,
        status=UserStatus.ACTIVE,
        last_login_at=datetime.now(UTC),
        latitude=request.latitude,
        longitude=request.longitude,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate token
    token_lifetime = get_settings().ACCESS_TOKEN_EXPIRE_MINUTES * 60
    access_token = create_access_token(user.id, token_version=user.token_version)

    # Find ward code if user is associated with a zone
    ward_code = None
    if user.zone_id:
        zone_code = db.scalar(select(Zone.code).where(Zone.id == user.zone_id))
        if zone_code:
            ward_code = zone_code

    auth_user = AuthenticatedUser(
        id=user.id,
        name=user.name,
        email=user.email,
        role=ROLE_MAP_DB_TO_FRONTEND.get(user.role, user.role.name),
        ward_code=ward_code,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": token_lifetime,
        "user": auth_user,
    }


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> Any:
    """Authenticate credentials and return session tokens."""
    # Find user by email, ignoring soft-deleted accounts
    user = db.scalar(
        select(User).where(
            User.email == request.email.lower(),
            User.deleted_at.is_(None),
        )
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Verify password hash
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Verify status is Active
    if user.status == UserStatus.DISABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been suspended by an administrator.",
        )

    # Update last login timestamp
    user.last_login_at = datetime.now(UTC)
    db.commit()
    db.refresh(user)

    # Generate token
    token_lifetime = get_settings().ACCESS_TOKEN_EXPIRE_MINUTES * 60
    access_token = create_access_token(user.id, token_version=user.token_version)

    # Find ward code
    ward_code = None
    if user.zone_id:
        zone_code = db.scalar(select(Zone.code).where(Zone.id == user.zone_id))
        if zone_code:
            ward_code = zone_code

    auth_user = AuthenticatedUser(
        id=user.id,
        name=user.name,
        email=user.email,
        role=ROLE_MAP_DB_TO_FRONTEND.get(user.role, user.role.name),
        ward_code=ward_code,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": token_lifetime,
        "user": auth_user,
    }


@router.get("/me", response_model=AuthenticatedUser)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Any:
    """Return the authenticated caller's profile details."""
    ward_code = None
    if current_user.zone_id:
        zone_code = db.scalar(select(Zone.code).where(Zone.id == current_user.zone_id))
        if zone_code:
            ward_code = zone_code

    return AuthenticatedUser(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=ROLE_MAP_DB_TO_FRONTEND.get(current_user.role, current_user.role.name),
        ward_code=ward_code,
    )
