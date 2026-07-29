"""Zone (ward) reference table.

Ward-code canonicalisation. User Story 1.1 requires that "W-04",
"w-04" and " W-04 " resolve to the same ward. A plain unique constraint on the
raw string treats those as three different wards, which breaks lookup, route
association and RBAC ward-scope. Two layers enforce canonical form:

  * a Python `validates` hook uppercases and strips on write, so the ORM can
    never persist a non-canonical value; and
  * a functional unique index plus CHECK constraints in the migration enforce
    it at the database, so a direct SQL write cannot bypass it either.

Non-blank enforcement: CHECK constraints reject empty or
whitespace-only name and code.

`sectors` is retained as a display string for the pilot. It is
explicitly NOT used for routing or scoping. If a later story needs to query or
scope by sector, promote it to its own table then; that decision is tracked as
a Jira item rather than solved speculatively now.

`manager_id` from the DBML is deliberately deferred until the officer/
admin assignment story lands; tracked in Jira.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base, Timestamps, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.models.user import User


class Zone(Base, UUIDPrimaryKey, Timestamps):
    __tablename__ = "zones"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # Canonical form (UPPER, trimmed) is enforced by the validator below and by
    # the functional unique index in the migration.
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    sectors: Mapped[str | None] = mapped_column(String(500))
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", name="fk_zones_manager_id_users"),
        nullable=True,
    )

    # Relationships
    manager: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[manager_id],
        back_populates="managed_zones",
    )
    members: Mapped[list["User"]] = relationship(
        "User",
        foreign_keys="[User.zone_id]",
        back_populates="zone",
    )

    __table_args__ = (
        CheckConstraint("length(btrim(name)) > 0", name="name_not_blank"),
        CheckConstraint("length(btrim(code)) > 0", name="code_not_blank"),
        # Reject any code that is not already canonical, as a backstop to the
        # ORM validator.
        CheckConstraint("code = upper(btrim(code))", name="code_is_canonical"),
        # Case/space-insensitive uniqueness. Because code is already forced to
        # canonical form above, a plain unique index would also work, but the
        # functional index documents intent and survives a bad direct write.
        Index("uq_zones_code_canonical", func.upper(func.btrim(text("code"))), unique=True),
    )

    @validates("code")
    def _canonicalise_code(self, _key: str, value: str) -> str:
        if value is None:
            return value
        return value.strip().upper()

    @validates("name")
    def _strip_name(self, _key: str, value: str) -> str:
        return value.strip() if value else value
