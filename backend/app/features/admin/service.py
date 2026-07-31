from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.features.admin.schemas import (
    AdminDashboardResponse,
    DashboardStats,
    LogEntry,
    LogsResponse,
    UserSummary,
    WardCreate,
    WardListResponse,
    WardResponse,
    WardUpdate,
)
from app.features.auth.dependencies import ROLE_MAP_DB_TO_FRONTEND
from app.features.users.models import User

# from app.models.audit import AuditLog
from app.models.audit import AuditLog, create_audit_log
from app.models.enums import Role
from app.models.zone import Zone


def get_dashboard_data(db: Session) -> AdminDashboardResponse:
    """Fetch all users and summary statistics for the admin dashboard."""

    # Get all users with their zone information
    users_with_zones = db.execute(
        select(User, Zone)
        .outerjoin(Zone, User.zone_id == Zone.id)
        .where(User.deleted_at.is_(None))
        .order_by(User.created_at.desc())
    ).all()

    user_summaries = []
    for user, zone in users_with_zones:
        user_summaries.append(
            UserSummary(
                id=user.id,
                name=user.name,
                email=user.email,
                phone=user.phone,
                role=ROLE_MAP_DB_TO_FRONTEND.get(user.role, user.role.name),
                zone_code=zone.code if zone else None,
                zone_name=zone.name if zone else None,
                zone_id=user.zone_id,
                last_login_at=user.last_login_at,
                status=user.status.name,
            )
        )

    # Calculate statistics
    registered_users = len(user_summaries)
    wards_configured = db.scalar(select(func.count(Zone.id))) or 0

    # For errors in 24h, we'll return 0 for now as we don't have error logging yet
    errors_in_24h = 0

    # System uptime - for now return a placeholder (hours since app start)
    # In production, this would be calculated from actual start time
    system_uptime_hours = 24

    stats = DashboardStats(
        registered_users=registered_users,
        wards_configured=wards_configured,
        errors_in_24h=errors_in_24h,
        system_uptime_hours=system_uptime_hours,
    )

    return AdminDashboardResponse(stats=stats, users=user_summaries)


def create_ward(
    db: Session,
    ward_data: WardCreate,
    user_id: str | None = None,
    user_name: str | None = None,
    ip_address: str | None = None,
) -> WardResponse:
    """Create a new ward."""

    # Check if ward code already exists
    existing_ward = db.scalar(select(Zone).where(Zone.code == ward_data.code.upper().strip()))
    if existing_ward:
        raise ValueError(f"Ward with code '{ward_data.code}' already exists")

    # Create new ward
    new_ward = Zone(
        code=ward_data.code,
        name=ward_data.name,
        sectors=ward_data.sectors,
    )

    db.add(new_ward)
    db.commit()
    db.refresh(new_ward)

    # Log ward creation (non-blocking, separate transaction)
    try:
        create_audit_log(
            db,
            actor_id=user_id,
            actor_name=user_name,
            actor_role="SYSTEM_ADMIN",
            action="WARD_CREATED",
            entity_type="Zone",
            entity_id=str(new_ward.id),
            module="admin",
            description=f"Ward {new_ward.code} created by admin",
            ip_address=ip_address,
        )
    except Exception as e:
        print(f"Audit log creation failed: {e}")

    return WardResponse(
        id=new_ward.id,
        code=new_ward.code,
        name=new_ward.name,
        sectors=new_ward.sectors,
        manager_id=new_ward.manager_id,
        manager_name=None,
        workers_count=0,
        created_at=new_ward.created_at,
        updated_at=new_ward.updated_at,
    )


def list_wards(db: Session) -> WardListResponse:
    """List all wards with their manager and worker counts."""

    wards = db.execute(select(Zone).order_by(Zone.code)).scalars().all()

    ward_responses = []
    for ward in wards:
        # Get manager name if assigned
        manager_name = None
        if ward.manager_id:
            manager = db.scalar(select(User).where(User.id == ward.manager_id))
            if manager:
                manager_name = manager.name

        # Count workers (collection workers assigned to this ward)
        workers_count = (
            db.scalar(
                select(func.count(User.id)).where(
                    User.zone_id == ward.id, User.role == Role.COLLECTION_WORKER
                )
            )
            or 0
        )

        ward_responses.append(
            WardResponse(
                id=ward.id,
                code=ward.code,
                name=ward.name,
                sectors=ward.sectors,
                manager_id=ward.manager_id,
                manager_name=manager_name,
                workers_count=workers_count,
                created_at=ward.created_at,
                updated_at=ward.updated_at,
            )
        )

    return WardListResponse(wards=ward_responses, total=len(ward_responses))


def update_ward(
    db: Session,
    ward_id: str,
    ward_data: WardUpdate,
    user_id: str | None = None,
    user_name: str | None = None,
    ip_address: str | None = None,
) -> WardResponse:
    """Update an existing ward."""

    # Find the ward
    ward = db.scalar(select(Zone).where(Zone.id == ward_id))
    if not ward:
        raise ValueError(f"Ward with ID '{ward_id}' not found")

    # Convert empty string to None for manager_id
    manager_id = ward_data.manager_id if ward_data.manager_id else None

    # If manager_id is provided, verify it exists and is a manager
    if manager_id:
        manager = db.scalar(
            select(User).where(
                User.id == manager_id,
                User.role == Role.MUNICIPAL_OFFICER,
                User.deleted_at.is_(None),
            )
        )
        if not manager:
            raise ValueError("Invalid manager ID or user is not a manager")

    # Track changes before update
    changes = []
    if ward.name != ward_data.name:
        changes.append(f"name to '{ward_data.name}'")
    if ward.sectors != ward_data.sectors:
        changes.append(f"sectors to '{ward_data.sectors}'")
    if ward.manager_id != manager_id:
        changes.append(f"manager to {'assigned' if manager_id else 'unassigned'}")

    # Update ward fields
    ward.name = ward_data.name
    ward.sectors = ward_data.sectors
    ward.manager_id = manager_id

    db.commit()
    db.refresh(ward)

    # Log ward update (non-blocking, separate transaction)
    try:
        create_audit_log(
            db,
            actor_id=user_id,
            actor_name=user_name,
            actor_role="SYSTEM_ADMIN",
            action="WARD_UPDATED",
            entity_type="Zone",
            entity_id=str(ward.id),
            module="admin",
            description=(
                f"Ward {ward.code} updated: {', '.join(changes) if changes else 'details modified'}"
            ),
            ip_address=ip_address,
        )
    except Exception as e:
        print(f"Audit log creation failed: {e}")

    # Get manager name if assigned
    manager_name = None
    if ward.manager_id:
        manager = db.scalar(select(User).where(User.id == ward.manager_id))
        if manager:
            manager_name = manager.name

    # Count workers
    workers_count = (
        db.scalar(
            select(func.count(User.id)).where(
                User.zone_id == ward.id, User.role == Role.COLLECTION_WORKER
            )
        )
        or 0
    )

    return WardResponse(
        id=ward.id,
        code=ward.code,
        name=ward.name,
        sectors=ward.sectors,
        manager_id=ward.manager_id,
        manager_name=manager_name,
        workers_count=workers_count,
        created_at=ward.created_at,
        updated_at=ward.updated_at,
    )


def delete_ward(
    db: Session,
    ward_id: str,
    user_id: str | None = None,
    user_name: str | None = None,
    ip_address: str | None = None,
) -> None:
    """Delete a ward."""
    import uuid

    # Convert ward_id to UUID
    try:
        ward_uuid = uuid.UUID(ward_id)
    except ValueError as err:
        raise ValueError(f"Invalid ward ID format: '{ward_id}'") from err

    # Find the ward
    ward = db.scalar(select(Zone).where(Zone.id == ward_uuid))
    if not ward:
        raise ValueError(f"Ward with ID '{ward_id}' not found")

    # Check if there are any users assigned to this ward
    user_count = db.scalar(select(func.count(User.id)).where(User.zone_id == ward_uuid)) or 0

    if user_count > 0:
        raise ValueError(f"Cannot delete ward with {user_count} assigned users")

    # Delete the ward
    db.delete(ward)
    db.commit()

    # Log ward deletion (non-blocking, separate transaction)
    try:
        create_audit_log(
            db,
            actor_id=user_id,
            actor_name=user_name,
            actor_role="SYSTEM_ADMIN",
            action="WARD_DELETED",
            entity_type="Zone",
            entity_id=str(ward.id),
            module="admin",
            description=f"Ward {ward.code} deleted by admin",
            ip_address=ip_address,
        )
    except Exception as e:
        print(f"Audit log creation failed: {e}")


def get_logs(db: Session, limit: int = 100) -> LogsResponse:
    """Get system logs from the audit_logs table."""

    try:
        # Query audit logs ordered by timestamp descending
        logs = (
            db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit))
            .scalars()
            .all()
        )

        log_entries = []
        for log in logs:
            log_entries.append(
                LogEntry(
                    id=log.id,
                    timestamp=log.created_at,
                    actor_id=log.actor_id,
                    actor_role=log.actor_role,
                    actor_name=log.actor_name,
                    action=log.action,
                    entity_type=log.entity_type,
                    entity_id=log.entity_id,
                    module=log.module,
                    description=log.description,
                    ip_address=log.ip_address,
                )
            )

        # Get total count
        total = db.scalar(select(func.count(AuditLog.id))) or 0

        return LogsResponse(logs=log_entries, total=total)
    except Exception:
        # Return empty logs if there's an error
        return LogsResponse(logs=[], total=0)
