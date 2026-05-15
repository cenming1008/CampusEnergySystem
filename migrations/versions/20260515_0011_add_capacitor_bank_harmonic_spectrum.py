"""add capacitor bank harmonic spectrum

Revision ID: 20260515_0011
Revises: 20260424_0010
Create Date: 2026-05-15
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260515_0011"
down_revision = "20260424_0010"
branch_labels = None
depends_on = None


CAPACITOR_BANK_HARMONIC_COLUMNS = {
    "voltage_harmonics_a": sa.Column("voltage_harmonics_a", sa.JSON(), nullable=True),
    "voltage_harmonics_b": sa.Column("voltage_harmonics_b", sa.JSON(), nullable=True),
    "voltage_harmonics_c": sa.Column("voltage_harmonics_c", sa.JSON(), nullable=True),
    "current_harmonics_a": sa.Column("current_harmonics_a", sa.JSON(), nullable=True),
    "current_harmonics_b": sa.Column("current_harmonics_b", sa.JSON(), nullable=True),
    "current_harmonics_c": sa.Column("current_harmonics_c", sa.JSON(), nullable=True),
}


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if not _table_exists("capacitor_bank_telemetry"):
        return
    for column_name, column in CAPACITOR_BANK_HARMONIC_COLUMNS.items():
        if not _has_column("capacitor_bank_telemetry", column_name):
            op.add_column("capacitor_bank_telemetry", column.copy())


def downgrade() -> None:
    if not _table_exists("capacitor_bank_telemetry"):
        return
    for column_name in reversed(tuple(CAPACITOR_BANK_HARMONIC_COLUMNS)):
        if _has_column("capacitor_bank_telemetry", column_name):
            op.drop_column("capacitor_bank_telemetry", column_name)
