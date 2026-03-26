"""industrial baseline guardrails

Revision ID: 20260325_0001
Revises:
Create Date: 2026-03-25 20:05:00
"""

from __future__ import annotations

from alembic import context
from alembic import op
import sqlalchemy as sa


revision = "20260325_0001"
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    if context.is_offline_mode():
        return False
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    if context.is_offline_mode():
        return False
    if not _table_exists(table_name):
        return True  # table not yet created, skip column additions
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _ensure_tables() -> None:
    """Ensure all core tables exist via SQLModel metadata (idempotent)."""
    from sqlmodel import SQLModel
    from app.models import tables  # noqa: F401
    bind = op.get_bind()
    SQLModel.metadata.create_all(bind, checkfirst=True)


def upgrade() -> None:
    _ensure_tables()
    if _has_column("alarm", "severity") is False:
        op.add_column("alarm", sa.Column("severity", sa.String(length=32), nullable=True, server_default="warning"))
    if _has_column("alarm", "category") is False:
        op.add_column("alarm", sa.Column("category", sa.String(length=64), nullable=True, server_default="threshold"))
    if _has_column("alarm", "source") is False:
        op.add_column("alarm", sa.Column("source", sa.String(length=64), nullable=True, server_default="telemetry"))
    if _has_column("alarm", "resolved_at") is False:
        op.add_column("alarm", sa.Column("resolved_at", sa.DateTime(), nullable=True))
    if _has_column("alarm", "resolved_by") is False:
        op.add_column("alarm", sa.Column("resolved_by", sa.String(length=255), nullable=True))
    if _has_column("alarm", "handling_note") is False:
        op.add_column("alarm", sa.Column("handling_note", sa.Text(), nullable=True))

    if _has_column("mqtt_ingestion_record", "raw_payload") is False:
        op.add_column("mqtt_ingestion_record", sa.Column("raw_payload", sa.Text(), nullable=True))
    if _has_column("mqtt_ingestion_record", "replay_count") is False:
        op.add_column(
            "mqtt_ingestion_record",
            sa.Column("replay_count", sa.Integer(), nullable=False, server_default="0"),
        )
    if _has_column("mqtt_ingestion_record", "last_replayed_at") is False:
        op.add_column("mqtt_ingestion_record", sa.Column("last_replayed_at", sa.DateTime(), nullable=True))

    if _has_column("user", "role") is False:
        op.add_column("user", sa.Column("role", sa.String(length=32), nullable=True, server_default="admin"))
        op.execute('UPDATE "user" SET role = \'admin\' WHERE role IS NULL')
    if _has_column("user", "location_scope") is False:
        op.add_column("user", sa.Column("location_scope", sa.Text(), nullable=True))
    if _has_column("user", "must_change_password") is False:
        op.add_column("user", sa.Column("must_change_password", sa.Boolean(), nullable=False, server_default="false"))
    if _has_column("user", "failed_login_attempts") is False:
        op.add_column("user", sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"))
    if _has_column("user", "locked_until") is False:
        op.add_column("user", sa.Column("locked_until", sa.DateTime(), nullable=True))
    if _has_column("user", "token_version") is False:
        op.add_column("user", sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"))
    if _has_column("user", "last_login_at") is False:
        op.add_column("user", sa.Column("last_login_at", sa.DateTime(), nullable=True))
    if _has_column("user", "last_password_changed_at") is False:
        op.add_column("user", sa.Column("last_password_changed_at", sa.DateTime(), nullable=True))

    op.execute('CREATE INDEX IF NOT EXISTS idx_user_role ON "user" (role)')
    op.execute('CREATE INDEX IF NOT EXISTS idx_user_locked_until ON "user" (locked_until)')
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_energydata_device_timestamp "
        "ON energydata (device_id, timestamp DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_energydata_energy_type_timestamp "
        "ON energydata (energy_type, timestamp DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_alarm_device_resolved_timestamp "
        "ON alarm (device_id, is_resolved, timestamp DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_device_ingestion_health_last_success "
        "ON device_ingestion_health (last_success_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_device_ingestion_health_last_failure "
        "ON device_ingestion_health (last_failure_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_event_action_created_at "
        "ON audit_event (action, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_event_actor_created_at "
        "ON audit_event (actor, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_event_outcome_created_at "
        "ON audit_event (outcome, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_mqtt_ingestion_record_device_received "
        "ON mqtt_ingestion_record (device_id, received_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_mqtt_ingestion_record_status_received "
        "ON mqtt_ingestion_record (status, received_at DESC)"
    )


def downgrade() -> None:
    raise RuntimeError("基线迁移不支持自动回滚，请通过备份或显式 migration 回退。")
