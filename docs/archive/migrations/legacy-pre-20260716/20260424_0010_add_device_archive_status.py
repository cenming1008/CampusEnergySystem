"""add device archive status

Revision ID: 20260424_0010
Revises: 20260424_0009
Create Date: 2026-04-24
"""

from alembic import op
import sqlalchemy as sa


revision = "20260424_0010"
down_revision = "20260424_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "device",
        sa.Column("archive_status", sa.String(length=32), nullable=False, server_default="complete"),
    )
    op.create_index(op.f("ix_device_archive_status"), "device", ["archive_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_device_archive_status"), table_name="device")
    op.drop_column("device", "archive_status")
