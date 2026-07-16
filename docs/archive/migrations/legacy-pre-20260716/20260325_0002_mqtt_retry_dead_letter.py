"""mqtt retry dead letter

Revision ID: 20260325_0002
Revises: 20260325_0001
Create Date: 2026-03-25 20:30:00
"""

from __future__ import annotations

from alembic import context
from alembic import op
import sqlalchemy as sa


revision = "20260325_0002"
down_revision = "20260325_0001"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    if context.is_offline_mode():
        return False
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    if _has_column("mqtt_ingestion_record", "retry_count") is False:
        op.add_column(
            "mqtt_ingestion_record",
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        )
    if _has_column("mqtt_ingestion_record", "next_retry_at") is False:
        op.add_column(
            "mqtt_ingestion_record",
            sa.Column("next_retry_at", sa.DateTime(), nullable=True),
        )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_mqtt_ingestion_record_next_retry_at "
        "ON mqtt_ingestion_record (next_retry_at)"
    )


def downgrade() -> None:
    raise RuntimeError("该迁移不支持自动回滚，请使用显式数据库回退流程。")
