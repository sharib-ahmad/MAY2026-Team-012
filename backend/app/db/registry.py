# app/db/registry.py
# Import all database models here to register them with SQLAlchemy Base.metadata

from app.db.base import Base
from app.features.bulk_pickups.models import BulkPickupRequest
from app.features.collection_ops.models import (
    DailyPickupSchedule,
    DailyPickupStop,
    DelayLog,
    MixedWasteTag,
    Pickup,
    RouteHistory,
)
from app.features.complaints.models import Ticket
from app.features.credits.models import Badge, Credit, CreditFactor, UserBadge
from app.features.materials.models import Batch, Inventory
from app.features.notifications.models import Notification
from app.features.reuse.models import ReuseClaim, ReuseImage, ReuseListing
from app.features.sorting_guide.models import WasteCategory
from app.features.users.models import User
from app.models.audit import AuditLog, TraceEvent
from app.models.enums import (
    Availability,
    BadgeCategory,
    BatchQuality,
    BatchStatus,
    BulkRequestStatus,
    CreditReason,
    CreditStatus,
    DelayReason,
    EntityType,
    ExportJobStatus,
    ExportJobType,
    PickupStatus,
    PickupStopStatus,
    ReuseCategory,
    ReuseClaimStatus,
    ReuseCondition,
    ReuseStatus,
    Role,
    TicketStatus,
    TicketType,
    TraceEventType,
    UserStatus,
    WasteSeverity,
)
from app.models.export import ExportJob
from app.models.zone import Zone
