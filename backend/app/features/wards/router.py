from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.features.admin.dependencies import require_admin
from app.features.admin.schemas import WardListResponse
from app.features.admin.service import list_wards
from app.features.users.models import User
from app.models.zone import Zone

router = APIRouter(tags=["Wards"])


@router.get("/wards", response_model=WardListResponse)
def list_admin_wards(
    current_user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> WardListResponse:
    """Canonical administrator ward list."""
    return list_wards(db)


@router.get("/zones")
def list_zones(db: Session = Depends(get_db)) -> Any:
    """Return a list of all active zones for reference."""
    zones = db.scalars(select(Zone).order_by(Zone.name)).all()
    return [{"id": str(z.id), "name": f"{z.code} - {z.name}"} for z in zones]
