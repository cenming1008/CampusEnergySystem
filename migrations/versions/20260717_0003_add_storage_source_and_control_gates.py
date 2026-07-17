"""add storage source and device control gates

Revision ID: 20260717_0003
Revises: 20260716_0002
Create Date: 2026-07-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260717_0003"
down_revision = "20260716_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "storage_asset_profile",
        sa.Column("ems_auto_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "storage_telemetry",
        sa.Column("simulation_run_id", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_storage_telemetry_simulation_run_id",
        "storage_telemetry",
        ["simulation_run_id"],
        unique=False,
    )
    op.add_column(
        "storage_dispatch_plan",
        sa.Column("data_source", sa.String(), nullable=False, server_default="calculated"),
    )
    op.add_column(
        "storage_dispatch_plan",
        sa.Column("simulation_run_id", sa.String(), nullable=True),
    )
    op.create_index(
        "ix_storage_dispatch_plan_simulation_run_id",
        "storage_dispatch_plan",
        ["simulation_run_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_storage_dispatch_plan_simulation_run_id", table_name="storage_dispatch_plan")
    op.drop_column("storage_dispatch_plan", "simulation_run_id")
    op.drop_column("storage_dispatch_plan", "data_source")
    op.drop_index("ix_storage_telemetry_simulation_run_id", table_name="storage_telemetry")
    op.drop_column("storage_telemetry", "simulation_run_id")
    op.drop_column("storage_asset_profile", "ems_auto_enabled")
