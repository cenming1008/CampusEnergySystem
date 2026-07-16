"""add capacitor bank monitor fields

Revision ID: 20260424_0009
Revises: 20260423_0008
Create Date: 2026-04-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260424_0009"
down_revision = "20260423_0008"
branch_labels = None
depends_on = None


CAPACITOR_BANK_CONTROL_PROFILE_COLUMNS = {
    "source": sa.Column("source", sa.String(), nullable=True),
    "snapshot_timestamp": sa.Column("snapshot_timestamp", sa.DateTime(), nullable=True),
    "phase_a_circuit_total_count": sa.Column("phase_a_circuit_total_count", sa.Integer(), nullable=True),
    "phase_b_circuit_total_count": sa.Column("phase_b_circuit_total_count", sa.Integer(), nullable=True),
    "phase_c_circuit_total_count": sa.Column("phase_c_circuit_total_count", sa.Integer(), nullable=True),
    "common_1_circuit_total_count": sa.Column("common_1_circuit_total_count", sa.Integer(), nullable=True),
    "common_2_circuit_total_count": sa.Column("common_2_circuit_total_count", sa.Integer(), nullable=True),
    "common_3_circuit_total_count": sa.Column("common_3_circuit_total_count", sa.Integer(), nullable=True),
    "phase_a_capacity_steps_kvar_json": sa.Column("phase_a_capacity_steps_kvar_json", sa.Text(), nullable=True),
    "phase_b_capacity_steps_kvar_json": sa.Column("phase_b_capacity_steps_kvar_json", sa.Text(), nullable=True),
    "phase_c_capacity_steps_kvar_json": sa.Column("phase_c_capacity_steps_kvar_json", sa.Text(), nullable=True),
    "common_1_capacity_steps_kvar_json": sa.Column("common_1_capacity_steps_kvar_json", sa.Text(), nullable=True),
    "common_2_capacity_steps_kvar_json": sa.Column("common_2_capacity_steps_kvar_json", sa.Text(), nullable=True),
    "common_3_capacity_steps_kvar_json": sa.Column("common_3_capacity_steps_kvar_json", sa.Text(), nullable=True),
    "phase_a_circuit_running_count": sa.Column("phase_a_circuit_running_count", sa.Integer(), nullable=True),
    "phase_b_circuit_running_count": sa.Column("phase_b_circuit_running_count", sa.Integer(), nullable=True),
    "phase_c_circuit_running_count": sa.Column("phase_c_circuit_running_count", sa.Integer(), nullable=True),
    "common_group_1_running_count": sa.Column("common_group_1_running_count", sa.Integer(), nullable=True),
    "common_group_2_running_count": sa.Column("common_group_2_running_count", sa.Integer(), nullable=True),
    "common_group_3_running_count": sa.Column("common_group_3_running_count", sa.Integer(), nullable=True),
    "split_circuit_running_count": sa.Column("split_circuit_running_count", sa.Integer(), nullable=True),
    "common_circuit_running_count": sa.Column("common_circuit_running_count", sa.Integer(), nullable=True),
    "running_circuit_count": sa.Column("running_circuit_count", sa.Integer(), nullable=True),
    "control_mode": sa.Column("control_mode", sa.String(length=32), nullable=True),
    "auto_on_elapsed_seconds": sa.Column("auto_on_elapsed_seconds", sa.Integer(), nullable=True),
    "auto_off_elapsed_seconds": sa.Column("auto_off_elapsed_seconds", sa.Integer(), nullable=True),
    "last_auto_action": sa.Column("last_auto_action", sa.String(length=64), nullable=True),
}

CAPACITOR_BANK_TELEMETRY_COLUMNS = {
    "phase_a_circuit_running_count": sa.Column("phase_a_circuit_running_count", sa.Integer(), nullable=True),
    "phase_b_circuit_running_count": sa.Column("phase_b_circuit_running_count", sa.Integer(), nullable=True),
    "phase_c_circuit_running_count": sa.Column("phase_c_circuit_running_count", sa.Integer(), nullable=True),
    "common_group_1_running_count": sa.Column("common_group_1_running_count", sa.Integer(), nullable=True),
    "common_group_2_running_count": sa.Column("common_group_2_running_count", sa.Integer(), nullable=True),
    "common_group_3_running_count": sa.Column("common_group_3_running_count", sa.Integer(), nullable=True),
    "split_circuit_running_count": sa.Column("split_circuit_running_count", sa.Integer(), nullable=True),
    "common_circuit_running_count": sa.Column("common_circuit_running_count", sa.Integer(), nullable=True),
    "running_circuit_count": sa.Column("running_circuit_count", sa.Integer(), nullable=True),
    "control_mode": sa.Column("control_mode", sa.String(length=32), nullable=True),
    "auto_on_elapsed_seconds": sa.Column("auto_on_elapsed_seconds", sa.Integer(), nullable=True),
    "auto_off_elapsed_seconds": sa.Column("auto_off_elapsed_seconds", sa.Integer(), nullable=True),
    "last_auto_action": sa.Column("last_auto_action", sa.String(length=64), nullable=True),
}


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _add_missing_columns(table_name: str, columns: dict[str, sa.Column]) -> None:
    if not _table_exists(table_name):
        return
    for column_name, column in columns.items():
        if not _has_column(table_name, column_name):
            op.add_column(table_name, column.copy())


def _drop_existing_columns(table_name: str, columns: dict[str, sa.Column]) -> None:
    if not _table_exists(table_name):
        return
    for column_name in reversed(tuple(columns)):
        if _has_column(table_name, column_name):
            op.drop_column(table_name, column_name)


def upgrade() -> None:
    _add_missing_columns("capacitor_bank_control_profile", CAPACITOR_BANK_CONTROL_PROFILE_COLUMNS)
    _add_missing_columns("capacitor_bank_telemetry", CAPACITOR_BANK_TELEMETRY_COLUMNS)


def downgrade() -> None:
    _drop_existing_columns("capacitor_bank_telemetry", CAPACITOR_BANK_TELEMETRY_COLUMNS)
    _drop_existing_columns("capacitor_bank_control_profile", CAPACITOR_BANK_CONTROL_PROFILE_COLUMNS)
