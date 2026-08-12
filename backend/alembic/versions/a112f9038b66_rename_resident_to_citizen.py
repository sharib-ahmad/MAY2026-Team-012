"""rename_resident_to_citizen

Revision ID: a112f9038b66
Revises: a3f8c2e1d905
Create Date: 2026-08-04 01:12:02.446638
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "a112f9038b66"
down_revision: str | None = "a3f8c2e1d905"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Rename columns to preserve existing data
    op.alter_column("daily_pickup_stops", "resident_id", new_column_name="citizen_id")
    op.alter_column("pickups", "resident_id", new_column_name="citizen_id")

    # Re-create indexes with new names
    op.drop_index("ix_daily_pickup_stops_resident_id", table_name="daily_pickup_stops")
    op.create_index(
        "ix_daily_pickup_stops_citizen_id", "daily_pickup_stops", ["citizen_id"], unique=False
    )

    op.drop_index("ix_pickups_resident_id", table_name="pickups")
    op.create_index("ix_pickups_citizen_id", "pickups", ["citizen_id"], unique=False)

    # Re-create foreign key constraints
    op.drop_constraint(
        "fk_daily_pickup_stops_resident_id_users", "daily_pickup_stops", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_daily_pickup_stops_citizen_id_users",
        "daily_pickup_stops",
        "users",
        ["citizen_id"],
        ["id"],
    )

    op.drop_constraint("fk_pickups_resident_id_users", "pickups", type_="foreignkey")
    op.create_foreign_key("fk_pickups_citizen_id_users", "pickups", "users", ["citizen_id"], ["id"])


def downgrade() -> None:
    # Revert renamed columns
    op.alter_column("daily_pickup_stops", "citizen_id", new_column_name="resident_id")
    op.alter_column("pickups", "citizen_id", new_column_name="resident_id")

    # Revert indexes
    op.drop_index("ix_daily_pickup_stops_citizen_id", table_name="daily_pickup_stops")
    op.create_index(
        "ix_daily_pickup_stops_resident_id", "daily_pickup_stops", ["resident_id"], unique=False
    )

    op.drop_index("ix_pickups_citizen_id", table_name="pickups")
    op.create_index("ix_pickups_resident_id", "pickups", ["resident_id"], unique=False)

    # Revert constraints
    op.drop_constraint(
        "fk_daily_pickup_stops_citizen_id_users", "daily_pickup_stops", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_daily_pickup_stops_resident_id_users",
        "daily_pickup_stops",
        "users",
        ["resident_id"],
        ["id"],
    )

    op.drop_constraint("fk_pickups_citizen_id_users", "pickups", type_="foreignkey")
    op.create_foreign_key(
        "fk_pickups_resident_id_users", "pickups", "users", ["resident_id"], ["id"]
    )
