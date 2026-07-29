"""Model registry.

Alembic's autogenerate compares the database against every model imported by
the time it inspects Base.metadata. A model that is not imported here is
INVISIBLE to autogenerate, and its table will silently never be migrated.

Therefore: every new model file must be imported here in the same PR that adds
it. This is the single most common cause of a "works locally, missing in CI"
migration bug, and importing here is how we prevent it.
"""

from app.db.base import Base
from app.models.audit import AuditLog, TraceEvent
from app.models.batch import Batch, Inventory
from app.models.credit import Badge, Credit, CreditFactor, UserBadge
from app.models.export import ExportJob
from app.models.notification import Notification
from app.models.pickup import (
    BulkPickupRequest,
    DailyPickupSchedule,
    DailyPickupStop,
    DelayLog,
    MixedWasteTag,
    Pickup,
    RouteHistory,
)
from app.models.reuse import ReuseClaim, ReuseImage, ReuseListing
from app.models.ticket import Ticket
from app.models.user import User
from app.models.waste_category import WasteCategory
from app.models.zone import Zone

__all__ = [
    "Base",
    "Zone",
    "User",
    "WasteCategory",
    "Pickup",
    "DailyPickupSchedule",
    "DailyPickupStop",
    "RouteHistory",
    "BulkPickupRequest",
    "DelayLog",
    "MixedWasteTag",
    "Ticket",
    "Batch",
    "Inventory",
    "CreditFactor",
    "Credit",
    "Badge",
    "UserBadge",
    "ReuseListing",
    "ReuseImage",
    "ReuseClaim",
    "Notification",
    "AuditLog",
    "TraceEvent",
    "ExportJob",
]
