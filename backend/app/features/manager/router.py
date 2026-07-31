from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.manager.dependencies import get_manager_zone_ids, require_manager
from app.features.manager.schemas import (
    ComplaintListResponse,
    ComplaintOut,
    ComplaintUpdate,
    ManagerOverviewResponse,
    RouteDetailOut,
    RouteListResponse,
    WorkerListResponse,
    WorkerOut,
    WorkerReassignRequest,
)
from app.features.manager.service import (
    get_overview,
    get_route_detail,
    list_complaints,
    list_routes,
    list_workers,
    reassign_worker,
    update_complaint,
)
from app.features.users.models import User

router = APIRouter(prefix="/manager", tags=["Manager"])


@router.get("/overview", response_model=ManagerOverviewResponse)
def get_manager_overview(
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> ManagerOverviewResponse:
    """Stats, ward roll-up, complaints trend, and priority queues for the
    manager's assigned wards (all wards for a system admin)."""
    zone_ids = get_manager_zone_ids(current_user, db)
    return get_overview(db, zone_ids)


@router.get("/complaints", response_model=ComplaintListResponse)
def get_manager_complaints(
    ward: str | None = None,
    status_filter: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> ComplaintListResponse:
    """List citizen complaints (tickets) within the manager's wards."""
    zone_ids = get_manager_zone_ids(current_user, db)
    return list_complaints(
        db,
        zone_ids,
        zone_code=ward,
        status=status_filter,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.patch("/complaints/{ticket_id}", response_model=ComplaintOut)
def patch_manager_complaint(
    ticket_id: str,
    update: ComplaintUpdate,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> ComplaintOut:
    """Advance, escalate-equivalent (reopen), or resolve a complaint."""
    zone_ids = get_manager_zone_ids(current_user, db)
    try:
        return update_complaint(db, ticket_id, update, current_user, zone_ids)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ValueError as e:
        code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(e).lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=str(e)) from e


@router.get("/routes", response_model=RouteListResponse)
def get_manager_routes(
    ward: str | None = None,
    status_filter: str | None = None,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> RouteListResponse:
    """Same-day route tracking: schedules, delay logs, and mixed-waste flags."""
    zone_ids = get_manager_zone_ids(current_user, db)
    return list_routes(db, zone_ids, zone_code=ward, status=status_filter)


@router.get("/routes/{schedule_id}", response_model=RouteDetailOut)
def get_manager_route_detail(
    schedule_id: str,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> RouteDetailOut:
    """Full detail for a single route, including its ordered stops."""
    zone_ids = get_manager_zone_ids(current_user, db)
    try:
        return get_route_detail(db, schedule_id, zone_ids)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/crews", response_model=WorkerListResponse)
def get_manager_crews(
    ward: str | None = None,
    availability: str | None = None,
    search: str | None = None,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> WorkerListResponse:
    """List collection workers within the manager's wards."""
    zone_ids = get_manager_zone_ids(current_user, db)
    return list_workers(db, zone_ids, zone_code=ward, availability=availability, search=search)


@router.patch("/crews/{worker_id}/reassign", response_model=WorkerOut)
def patch_manager_crew_reassign(
    worker_id: str,
    req: WorkerReassignRequest,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db),
) -> WorkerOut:
    """Move a worker to another ward, availability state, or both."""
    zone_ids = get_manager_zone_ids(current_user, db)
    try:
        return reassign_worker(db, worker_id, req, zone_ids)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except ValueError as e:
        code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(e).lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=str(e)) from e
