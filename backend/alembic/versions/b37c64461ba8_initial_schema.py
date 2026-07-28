"""initial schema

Revision ID: b37c64461ba8
Revises:
Create Date: 2026-07-25 18:40:19.865392
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "b37c64461ba8"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Reviewed and named per the metadata naming convention.
    op.create_table(
        "zones",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("sectors", sa.String(length=500), nullable=True),
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("code = upper(btrim(code))", name=op.f("ck_zones_code_is_canonical")),
        sa.CheckConstraint("length(btrim(code)) > 0", name=op.f("ck_zones_code_not_blank")),
        sa.CheckConstraint("length(btrim(name)) > 0", name=op.f("ck_zones_name_not_blank")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_zones")),
    )
    op.create_index(
        "uq_zones_code_canonical", "zones", [sa.text("upper(btrim(code))")], unique=True
    )


def downgrade() -> None:
    # Reviewed and named per the metadata naming convention.
    op.drop_index("uq_zones_code_canonical", table_name="zones")
    op.drop_table("zones")
