from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.session import get_db
from app.features.admin.dependencies import require_admin
from app.features.admin.schemas import (
    AdminDashboardResponse,
    LogsResponse,
    WardCreate,
    WardListResponse,
    WardResponse,
    WardUpdate,
)
from app.features.admin.service import (
    create_ward,
    delete_ward,
    get_dashboard_data,
    get_logs,
    list_wards,
    update_ward,
)
from app.features.auth.dependencies import ROLE_MAP_DB_TO_FRONTEND
from app.features.auth.schemas import AuthenticatedUser
from app.models.audit import create_audit_log
from app.models.enums import Role, UserStatus
from app.models.zone import Zone

if TYPE_CHECKING:
    from app.features.users.models import User

# Map frontend role strings to backend Role enums
ROLE_MAP_FRONTEND_TO_DB = {
    "RESIDENT": Role.CITIZEN,
    "COLLECTOR": Role.COLLECTION_WORKER,
    "RECYCLER": Role.RECYCLER,
    "MANAGER": Role.MUNICIPAL_OFFICER,
    "ADMIN": Role.SYSTEM_ADMIN,
}


class CreateAccountRequest(BaseModel):
    name: str
    email: str
    phone: str | None = None
    role: str
    zone_id: str | None = None
    password: str


class UserStatusUpdate(BaseModel):
    status: UserStatus


class UserCreate(BaseModel):
    name: str
    email: str
    phone: str
    role: str
    zone_id: str | None = None
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    role: str | None = None


router = APIRouter(tags=["Admin"])


@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    current_user: "User" = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminDashboardResponse:
    """Get admin dashboard data including all users and summary statistics."""
    return get_dashboard_data(db)


@router.get("/ward", response_model=WardListResponse)
def get_wards(
    current_user: "User" = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WardListResponse:
    """List all wards with their manager and worker counts."""
    return list_wards(db)


@router.post("/ward", response_model=WardResponse, status_code=status.HTTP_201_CREATED)
def create_new_ward(
    ward_data: WardCreate,
    req: Request,
    current_user: "User" = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WardResponse:
    """Create a new ward."""
    try:
        client_ip = req.client.host if req.client else None
        return create_ward(
            db,
            ward_data,
            user_id=str(current_user.id),
            user_name=current_user.name,
            ip_address=client_ip,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


@router.patch("/ward/{ward_id}", response_model=WardResponse)
def update_ward_endpoint(
    ward_id: str,
    ward_data: WardUpdate,
    req: Request,
    current_user: "User" = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WardResponse:
    """Update an existing ward."""
    try:
        client_ip = req.client.host if req.client else None
        return update_ward(
            db,
            ward_id,
            ward_data,
            user_id=str(current_user.id),
            user_name=current_user.name,
            ip_address=client_ip,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if "not found" in str(e).lower()
            else status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.delete("/ward/{ward_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ward_endpoint(
    ward_id: str,
    req: Request,
    current_user: "User" = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    """Delete a ward."""
    try:
        client_ip = req.client.host if req.client else None
        delete_ward(
            db,
            ward_id,
            user_id=str(current_user.id),
            user_name=current_user.name,
            ip_address=client_ip,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
            if "not found" in str(e).lower()
            else status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/account", response_model=dict)
def create_account(
    account_data: CreateAccountRequest,
    req: Request,
    current_user: "User" = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Create a new MANAGER or ADMIN account."""
    import uuid

    from app.features.users.models import User

    # Check if email is already registered
    existing_user_email = db.scalar(
        select(User).where(User.email == account_data.email.lower(), User.deleted_at.is_(None))
    )
    if existing_user_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Check if phone is already registered
    if account_data.phone:
        existing_user_phone = db.scalar(
            select(User).where(User.phone == account_data.phone, User.deleted_at.is_(None))
        )
        if existing_user_phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this phone number already exists.",
            )

    # Resolve database Role enum from input
    db_role = ROLE_MAP_FRONTEND_TO_DB.get(account_data.role)
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported role: {account_data.role}",
        )

    # Only allow MANAGER and ADMIN roles
    if db_role not in [Role.MUNICIPAL_OFFICER, Role.SYSTEM_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only MANAGER and ADMIN accounts can be created by administrators.",
        )

    # If zone_id is provided, verify it exists
    zone_uuid = None
    if account_data.zone_id:
        try:
            zone_uuid = uuid.UUID(account_data.zone_id)
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid zone ID format.",
            ) from err
        zone = db.scalar(select(Zone).where(Zone.id == zone_uuid))
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Selected ward does not exist.",
            )

    # Hash the password and create the user
    hashed_password = get_password_hash(account_data.password)
    user = User(
        name=account_data.name,
        email=account_data.email.lower(),
        password_hash=hashed_password,
        phone=account_data.phone,
        role=db_role,
        zone_id=zone_uuid,
        status=UserStatus.ACTIVE,
        last_login_at=datetime.now(UTC),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Log account creation (non-blocking)
    try:
        client_ip = req.client.host if req.client else None
        create_audit_log(
            db,
            actor_id=str(current_user.id),
            actor_name=current_user.name,
            actor_role=current_user.role.name,
            action="ACCOUNT_CREATED",
            entity_type="User",
            entity_id=str(user.id),
            module="admin",
            description=f"Admin created {user.role.name} account: {user.email}",
            ip_address=client_ip,
        )
    except Exception:
        # Ignore audit logging errors
        pass

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

    return {"user": auth_user}


@router.get("/logs", response_model=LogsResponse)
def get_admin_logs(
    current_user: "User" = Depends(require_admin),
    db: Session = Depends(get_db),
    limit: int = 100,
) -> LogsResponse:
    """Get system logs for admin monitoring."""
    return get_logs(db, limit)


@router.patch("/user/{user_id}/status")
def update_user_status(
    user_id: str,
    status_update: UserStatusUpdate,
    req: Request,
    current_user: "User" = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Update a user's status (suspend/activate)."""
    import uuid

    from sqlalchemy import select

    from app.features.users.models import User

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        ) from err

    user = db.scalar(select(User).where(User.id == user_uuid))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    old_status = user.status
    user.status = status_update.status
    db.commit()
    db.refresh(user)

    # Log status change (non-blocking)
    try:
        client_ip = req.client.host if req.client else None
        create_audit_log(
            db,
            actor_id=str(current_user.id),
            actor_name=current_user.name,
            actor_role=current_user.role.name,
            action="USER_STATUS_CHANGED",
            entity_type="User",
            entity_id=str(user.id),
            module="admin",
            description=f"User {user.email} status changed from {old_status} to {user.status}",
            ip_address=client_ip,
        )
    except Exception as e:
        print(f"Audit log creation failed: {e}")

    return {"message": "User status updated successfully", "status": user.status}


@router.delete("/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    req: Request,
    current_user: "User" = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    """Delete a user account."""
    import uuid

    from sqlalchemy import select

    from app.features.users.models import User

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        ) from err

    user = db.scalar(select(User).where(User.id == user_uuid))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent deleting yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    # Store user details for audit log before deletion
    user_email = user.email
    user_name = user.name

    db.delete(user)
    db.commit()

    # Log user deletion (non-blocking)
    try:
        client_ip = req.client.host if req.client else None
        create_audit_log(
            db,
            actor_id=str(current_user.id),
            actor_name=current_user.name,
            actor_role=current_user.role.name,
            action="USER_DELETED",
            entity_type="User",
            entity_id=str(user_uuid),
            module="admin",
            description=f"User {user_email} ({user_name}) deleted by admin",
            ip_address=client_ip,
        )
    except Exception as e:
        print(f"Audit log creation failed: {e}")


@router.post("/user")
def create_user(
    user_data: UserCreate,
    req: Request,
    current_user: "User" = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Create a new user."""
    import uuid

    from sqlalchemy import select

    from app.features.users.models import User

    # Check if email is already used by another user
    existing_user = db.scalar(
        select(User).where(User.email == user_data.email.lower(), User.deleted_at.is_(None))
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already in use by another user"
        )

    # Check if phone is already used by another user
    existing_user = db.scalar(
        select(User).where(User.phone == user_data.phone, User.deleted_at.is_(None))
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already in use by another user",
        )

    # If zone_id is provided, verify it exists
    zone_uuid = None
    if user_data.zone_id:
        try:
            zone_uuid = uuid.UUID(user_data.zone_id)
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid zone ID format.",
            ) from err
        zone = db.scalar(select(Zone).where(Zone.id == zone_uuid))
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Selected ward does not exist.",
            )

    # Resolve the frontend role string to the database Role enum.
    db_role = ROLE_MAP_FRONTEND_TO_DB.get(user_data.role)
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported role: {user_data.role}",
        )

    # Hash the password and create the user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        name=user_data.name,
        email=user_data.email.lower(),
        password_hash=hashed_password,
        phone=user_data.phone,
        role=db_role,
        zone_id=zone_uuid,
        status=UserStatus.ACTIVE,
        last_login_at=datetime.now(UTC),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Log account creation (non-blocking)
    try:
        client_ip = req.client.host if req.client else None
        create_audit_log(
            db,
            actor_id=str(current_user.id),
            actor_name=current_user.name,
            actor_role=current_user.role.name,
            action="ACCOUNT_CREATED",
            entity_type="User",
            entity_id=str(user.id),
            module="admin",
            description=f"Admin created {user.role.name} account: {user.email}",
            ip_address=client_ip,
        )
    except Exception:
        # Ignore audit logging errors
        pass

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

    return {"user": auth_user}


@router.patch("/user/{user_id}")
def update_user(
    user_id: str,
    user_update: UserUpdate,
    req: Request,
    current_user: "User" = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Update a user's details."""
    import uuid

    from sqlalchemy import select

    from app.features.users.models import User

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        ) from err

    user = db.scalar(select(User).where(User.id == user_uuid))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Track changes for audit log
    changes = []

    print(f"Updating user {user_uuid}")
    print(f"Current user: email={user.email}, phone={user.phone}")
    print(
        f"Update data: email={user_update.email}, "
        f"phone={user_update.phone}, name={user_update.name}, role={user_update.role}"
    )

    # Update fields if provided
    if user_update.name is not None and user_update.name != user.name:
        changes.append(f"name from '{user.name}' to '{user_update.name}'")
        user.name = user_update.name
    if user_update.email is not None and user_update.email.lower() != user.email.lower():
        # Check if email is already used by another user
        from sqlalchemy import select

        existing_user = db.scalar(
            select(User).where(
                User.email == user_update.email.lower(),
                User.id != user_uuid,
                User.deleted_at.is_(None),
            )
        )
        if existing_user:
            print(
                f"Email conflict: trying to set {user_update.email.lower()} "
                f"but user {existing_user.id} already has it"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already in use by another user"
            )
        changes.append(f"email from '{user.email}' to '{user_update.email}'")
        user.email = user_update.email.lower()
    if user_update.phone is not None and user_update.phone != user.phone:
        # Check if phone is already used by another user
        from sqlalchemy import select

        existing_user = db.scalar(
            select(User).where(
                User.phone == user_update.phone,
                User.id != user_uuid,
                User.deleted_at.is_(None),
            )
        )
        if existing_user:
            print(
                f"Phone conflict: trying to set {user_update.phone} "
                f"but user {existing_user.id} already has it"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number already in use by another user",
            )
        changes.append(f"phone from '{user.phone}' to '{user_update.phone}'")
        user.phone = user_update.phone
    if user_update.role is not None:
        new_role = ROLE_MAP_FRONTEND_TO_DB.get(user_update.role)
        if new_role and new_role != user.role:
            changes.append(f"role from '{user.role.name}' to '{new_role.name}'")
            user.role = new_role

    db.commit()
    db.refresh(user)

    # Log user update (non-blocking)
    try:
        client_ip = req.client.host if req.client else None
        create_audit_log(
            db,
            actor_id=str(current_user.id),
            actor_name=current_user.name,
            actor_role=current_user.role.name,
            action="USER_UPDATED",
            entity_type="User",
            entity_id=str(user.id),
            module="admin",
            description=(
                f"User {user.email} updated: {', '.join(changes) if changes else 'no changes'}"
            ),
            ip_address=client_ip,
        )
    except Exception as e:
        print(f"Audit log creation failed: {e}")

    return {"message": "User updated successfully"}
