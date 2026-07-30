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
from app.models.zone import Zone

__all__ = [
    "Base",
    "AuditLog",
    "TraceEvent",
    "Zone",
]
