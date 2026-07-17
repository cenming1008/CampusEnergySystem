"""add storage simulation persistence contracts

Revision ID: 20260716_0002
Revises: 20260716_0001
Create Date: 2026-07-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260716_0002"
down_revision = "20260716_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "storage_asset_profile",
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("rated_energy_kwh", sa.Float(), nullable=False),
        sa.Column("rated_power_kw", sa.Float(), nullable=False),
        sa.Column("max_charge_power_kw", sa.Float(), nullable=True),
        sa.Column("max_discharge_power_kw", sa.Float(), nullable=True),
        sa.Column("charge_efficiency", sa.Float(), nullable=False),
        sa.Column("discharge_efficiency", sa.Float(), nullable=False),
        sa.Column("soc_min", sa.Float(), nullable=False),
        sa.Column("soc_max", sa.Float(), nullable=False),
        sa.Column("soc_soft_min", sa.Float(), nullable=False),
        sa.Column("soc_soft_max", sa.Float(), nullable=False),
        sa.Column("rated_ac_voltage", sa.Float(), nullable=True),
        sa.Column("rated_dc_voltage", sa.Float(), nullable=True),
        sa.Column("battery_type", sa.String(), nullable=True),
        sa.Column("bms_model", sa.String(), nullable=True),
        sa.Column("pcs_model", sa.String(), nullable=True),
        sa.Column("protocol_version", sa.String(), nullable=True),
        sa.Column("installation_location", sa.String(), nullable=True),
        sa.Column("commission_date", sa.Date(), nullable=True),
        sa.Column("data_source", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["device.id"]),
        sa.PrimaryKeyConstraint("device_id"),
    )
    op.create_table(
        "storage_dispatch_plan",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("dispatch_date", sa.Date(), nullable=False),
        sa.Column("slot_index", sa.Integer(), nullable=False),
        sa.Column("interval_minutes", sa.Integer(), nullable=False),
        sa.Column("target_active_power", sa.Float(), nullable=False),
        sa.Column("forecast_load_power", sa.Float(), nullable=True),
        sa.Column("forecast_pv_power", sa.Float(), nullable=True),
        sa.Column("tariff_price", sa.Float(), nullable=True),
        sa.Column("expected_soc", sa.Float(), nullable=True),
        sa.Column("strategy", sa.String(), nullable=False),
        sa.Column("strategy_version", sa.String(), nullable=False),
        sa.Column("solver_status", sa.String(), nullable=False),
        sa.Column("is_valid", sa.Boolean(), nullable=False),
        sa.Column("failure_reason", sa.String(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["device_id"], ["device.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "device_id",
            "dispatch_date",
            "slot_index",
            name="uq_storage_dispatch_device_date_slot",
        ),
    )
    op.add_column(
        "storage_telemetry",
        sa.Column("target_active_power", sa.Float(), nullable=True),
    )
    op.add_column(
        "storage_telemetry",
        sa.Column("available_charge_power", sa.Float(), nullable=True),
    )
    op.add_column(
        "storage_telemetry",
        sa.Column("available_discharge_power", sa.Float(), nullable=True),
    )
    op.add_column(
        "storage_telemetry",
        sa.Column("bms_status", sa.String(), nullable=True),
    )
    op.add_column(
        "storage_telemetry",
        sa.Column("pcs_status", sa.String(), nullable=True),
    )
    op.add_column(
        "storage_telemetry",
        sa.Column("grid_status", sa.String(), nullable=True),
    )
    op.add_column(
        "storage_telemetry",
        sa.Column("command_source", sa.String(), nullable=True),
    )
    op.add_column(
        "storage_telemetry",
        sa.Column(
            "data_source",
            sa.String(),
            nullable=False,
            server_default="telemetry",
        ),
    )


def downgrade() -> None:
    op.drop_column("storage_telemetry", "data_source")
    op.drop_column("storage_telemetry", "command_source")
    op.drop_column("storage_telemetry", "grid_status")
    op.drop_column("storage_telemetry", "pcs_status")
    op.drop_column("storage_telemetry", "bms_status")
    op.drop_column("storage_telemetry", "available_discharge_power")
    op.drop_column("storage_telemetry", "available_charge_power")
    op.drop_column("storage_telemetry", "target_active_power")
    op.drop_table("storage_dispatch_plan")
    op.drop_table("storage_asset_profile")
