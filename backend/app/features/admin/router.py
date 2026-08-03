from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.session import get_db
from app.features.admin.dependencies import require_admin
from app.features.admin.schemas import (
    AdminDashboardResponse,
    CreditFactorResponse,
    CreditFactorUpdate,
    LogsResponse,
    WardCreate,
    WardListResponse,
    WardResponse,
    WardUpdate,
)
from app.features.admin.schemas import (
    UserCreate as AdminUserCreate,
)
from app.features.admin.schemas import (
    UserStatusUpdate as AdminUserStatusUpdate,
)
from app.features.admin.schemas import (
    UserUpdate as AdminUserUpdate,
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
from app.features.credits.models import CreditFactor
from app.features.sorting_guide.models import WasteCategory
from app.models.audit import create_audit_log
from app.models.enums import Role, UserStatus
from app.models.zone import Zone

if TYPE_CHECKING:
    from app.features.users.models import User

# Admin requests use the canonical database role names.
ROLE_MAP_FRONTEND_TO_DB = {role.value: role for role in Role}


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


@router.get("/credit-factors", response_model=list[CreditFactorResponse])
def list_credit_factors(
    current_user: "User" = Depends(require_admin), db: Session = Depends(get_db)
) -> list[dict]:
    """List the per-kilogram reward rates used when a recycler processes a batch."""
    del current_user
    rows = db.execute(
        select(WasteCategory, CreditFactor)
        .outerjoin(CreditFactor, CreditFactor.category == WasteCategory.code)
        .order_by(WasteCategory.sort_order)
    ).all()
    return [
        {
            "category": category.code,
            "category_label": category.label,
            "credit_rate": float(factor.credit_rate) if factor else 0.0,
            "co2_factor": float(factor.co2_factor) if factor else 0.0,
            "description": factor.description if factor else None,
        }
        for category, factor in rows
    ]


@router.patch("/credit-factors/{category}", response_model=CreditFactorResponse)
def update_credit_factor(
    category: str,
    payload: CreditFactorUpdate,
    current_user: "User" = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Update a category's reward points per kilogram for future processing."""
    category_code = category.upper()
    factor = db.scalar(select(CreditFactor).where(CreditFactor.category == category_code))
    if not factor:
        category_row = db.scalar(select(WasteCategory).where(WasteCategory.code == category_code))
        if not category_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Waste category not found.",
            )
        factor = CreditFactor(category=category_code, credit_rate=0, co2_factor=0)
        db.add(factor)
    factor.credit_rate = payload.credit_rate
    factor.co2_factor = payload.co2_factor
    db.commit()
    db.refresh(factor)
    category_row = db.scalar(select(WasteCategory).where(WasteCategory.code == factor.category))
    return {
        "category": factor.category,
        "category_label": category_row.label if category_row else factor.category,
        "credit_rate": float(factor.credit_rate),
        "co2_factor": float(factor.co2_factor),
        "description": factor.description,
    }


@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    current_user: "User" = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminDashboardResponse:
    """Get admin dashboard data including all users and summary statistics."""
    return get_dashboard_data(db)


@router.get("/wards", response_model=WardListResponse)
@router.get("/ward", response_model=WardListResponse, include_in_schema=False)
def get_wards(
    current_user: "User" = Depends(require_admin),
    db: Session = Depends(get_db),
) -> WardListResponse:
    """List all wards with their manager and worker counts."""
    return list_wards(db)


@router.post("/wards", response_model=WardResponse, status_code=status.HTTP_201_CREATED)
@router.post(
    "/ward",
    response_model=WardResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
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


@router.patch("/wards/{ward_id}", response_model=WardResponse)
@router.patch("/ward/{ward_id}", response_model=WardResponse, include_in_schema=False)
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


@router.delete("/wards/{ward_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/ward/{ward_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
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
    """Create a new MUNICIPAL_OFFICER or SYSTEM_ADMIN account."""
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

    # Only allow municipal-officer and system-admin roles.
    if db_role not in [Role.MUNICIPAL_OFFICER, Role.SYSTEM_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Only MUNICIPAL_OFFICER and SYSTEM_ADMIN accounts can be created by administrators."
            ),
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


@router.patch("/users/{user_id}/status")
@router.patch("/user/{user_id}/status", include_in_schema=False)
def update_user_status(
    user_id: UUID,
    status_update: AdminUserStatusUpdate,
    req: Request,
    current_user: "User" = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Update a user's status (suspend/activate)."""
    from app.features.users.models import User

    user = db.scalar(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    old_status = user.status
    if (
        old_status == UserStatus.ACTIVE
        and status_update.status == UserStatus.DISABLED
        and user.role == Role.SYSTEM_ADMIN
        and db.scalar(
            select(func.count(User.id)).where(
                User.role == Role.SYSTEM_ADMIN,
                User.status == UserStatus.ACTIVE,
                User.deleted_at.is_(None),
            )
        )
        <= 1
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="LAST_ACTIVE_ADMIN")
    user.status = status_update.status
    user.token_version += 1
    create_audit_log(
        db,
        actor_id=str(current_user.id),
        actor_name=current_user.name,
        actor_role=current_user.role.value,
        action="USER_STATUS_CHANGED",
        entity_type="User",
        entity_id=str(user.id),
        module="admin",
        description=f"User {user.email} status changed from {old_status} to {user.status}",
        ip_address=req.client.host if req.client else None,
        commit=False,
        required=True,
    )
    db.commit()
    db.refresh(user)

    return {"message": "User status updated successfully", "status": user.status}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
def delete_user(
    user_id: UUID,
    req: Request,
    current_user: "User" = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    """Delete a user account."""
    from app.features.users.models import User

    user_uuid = user_id
    user = db.scalar(select(User).where(User.id == user_uuid, User.deleted_at.is_(None)))
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
    create_audit_log(
        db,
        actor_id=str(current_user.id),
        actor_name=current_user.name,
        actor_role=current_user.role.value,
        action="USER_DELETED",
        entity_type="User",
        entity_id=str(user_uuid),
        module="admin",
        description=f"User {user_email} ({user_name}) deleted by admin",
        ip_address=req.client.host if req.client else None,
        commit=False,
        required=True,
    )
    db.commit()


@router.post("/users", status_code=status.HTTP_201_CREATED)
@router.post("/user", status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_user(
    user_data: AdminUserCreate,
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
    )

    db.add(user)
    # The user ID is server-generated, so flush before recording an audit row
    # that references it. Both records are committed atomically below.
    db.flush()
    create_audit_log(
        db,
        actor_id=str(current_user.id),
        actor_name=current_user.name,
        actor_role=current_user.role.value,
        action="ACCOUNT_CREATED",
        entity_type="User",
        entity_id=str(user.id),
        module="admin",
        description=f"Admin created {user.role.name} account: {user.email}",
        ip_address=req.client.host if req.client else None,
        commit=False,
        required=True,
    )
    db.commit()
    db.refresh(user)

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


@router.patch("/users/{user_id}")
@router.patch("/user/{user_id}", include_in_schema=False)
def update_user(
    user_id: UUID,
    user_update: AdminUserUpdate,
    req: Request,
    current_user: "User" = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    """Update a user's details."""
    from app.features.users.models import User

    user_uuid = user_id
    user = db.scalar(select(User).where(User.id == user_uuid, User.deleted_at.is_(None)))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Track changes for audit log
    changes = []

    # Update fields if provided
    if user_update.name is not None and user_update.name != user.name:
        changes.append(f"name from '{user.name}' to '{user_update.name}'")
        user.name = user_update.name
    if user_update.email is not None and user_update.email.lower() != user.email.lower():
        # Check if email is already used by another user
        existing_user = db.scalar(
            select(User).where(
                User.email == user_update.email.lower(),
                User.id != user_uuid,
                User.deleted_at.is_(None),
            )
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already in use by another user"
            )
        changes.append(f"email from '{user.email}' to '{user_update.email}'")
        user.email = user_update.email.lower()
    if user_update.phone is not None and user_update.phone != user.phone:
        # Check if phone is already used by another user
        existing_user = db.scalar(
            select(User).where(
                User.phone == user_update.phone,
                User.id != user_uuid,
                User.deleted_at.is_(None),
            )
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phone number already in use by another user",
            )
        changes.append(f"phone from '{user.phone}' to '{user_update.phone}'")
        user.phone = user_update.phone
    if user_update.role is not None:
        new_role = ROLE_MAP_FRONTEND_TO_DB.get(user_update.role)
        if new_role and new_role != user.role:
            if (
                user.role == Role.SYSTEM_ADMIN
                and user.status == UserStatus.ACTIVE
                and db.scalar(
                    select(func.count(User.id)).where(
                        User.role == Role.SYSTEM_ADMIN,
                        User.status == UserStatus.ACTIVE,
                        User.deleted_at.is_(None),
                    )
                )
                <= 1
            ):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="LAST_ACTIVE_ADMIN"
                )
            changes.append(f"role from '{user.role.name}' to '{new_role.name}'")
            user.role = new_role
            user.token_version += 1

    create_audit_log(
        db,
        actor_id=str(current_user.id),
        actor_name=current_user.name,
        actor_role=current_user.role.value,
        action="USER_UPDATED",
        entity_type="User",
        entity_id=str(user.id),
        module="admin",
        description=f"User {user.email} updated: {', '.join(changes) if changes else 'no changes'}",
        ip_address=req.client.host if req.client else None,
        commit=False,
        required=True,
    )
    db.commit()
    db.refresh(user)

    return {"message": "User updated successfully"}
