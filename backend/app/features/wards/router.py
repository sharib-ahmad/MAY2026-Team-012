from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.zone import Zone

router = APIRouter(tags=["Wards"])


@router.get("/zones")
def list_zones(db: Session = Depends(get_db)) -> Any:
    """Return a list of all active zones for reference."""
    zones = db.scalars(select(Zone).order_by(Zone.name)).all()
    return [{"id": str(z.id), "name": f"{z.code} - {z.name}"} for z in zones]
