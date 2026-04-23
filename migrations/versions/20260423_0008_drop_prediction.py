"""drop prediction table after forecast removal

Revision ID: 20260423_0008
Revises: 20260414_0007
Create Date: 2026-04-23

This migration is intentionally destructive: forecast/LSTM has been removed
from the product surface and historical prediction rows are no longer kept.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260423_0008"
down_revision = "20260414_0007"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if _table_exists("prediction"):
        op.drop_table("prediction")


def downgrade() -> None:
    if _table_exists("prediction"):
        return

    op.create_table(
        "prediction",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prediction_type", sa.String(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=True),
        sa.Column("forecast_time", sa.DateTime(), nullable=False),
        sa.Column("predicted_value", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("actual_value", sa.Float(), nullable=True),
        sa.Column("algorithm", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("meta_info", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["device_id"], ["device.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_prediction_prediction_type", "prediction", ["prediction_type"], unique=False)
    op.create_index("ix_prediction_device_id", "prediction", ["device_id"], unique=False)
    op.create_index("ix_prediction_forecast_time", "prediction", ["forecast_time"], unique=False)
    op.create_index("ix_prediction_created_at", "prediction", ["created_at"], unique=False)
