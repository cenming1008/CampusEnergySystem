"""add device_subtype for compensation device modeling

Revision ID: 20260414_0007
Revises: 20260414_0006
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260414_0007"
down_revision = "20260414_0006"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_index(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if not _has_column("device", "device_subtype"):
        op.add_column("device", sa.Column("device_subtype", sa.String(length=64), nullable=True))
    if not _has_index("device", "ix_device_device_subtype"):
        op.create_index("ix_device_device_subtype", "device", ["device_subtype"], unique=False)

    op.execute(
        sa.text(
            """
            UPDATE device
            SET device_subtype = 'capacitor_bank_controller',
                device_category = 'compensation',
                device_type = 'capacitor_bank_controller'
            WHERE device_type IN ('reactive_power_compensator', 'compensation', 'capacitor_bank_controller')
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE device d
            SET device_subtype = 'svg',
                device_category = 'compensation',
                device_type = 'svg'
            WHERE d.device_subtype IS NULL
              AND d.device_type = 'svg'
              AND EXISTS (
                SELECT 1 FROM svg_asset_profile sap WHERE sap.device_id = d.id
              )
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE device d
            SET device_subtype = 'svg',
                device_category = 'compensation',
                device_type = 'svg'
            WHERE d.device_subtype IS NULL
              AND d.device_type = 'svg'
              AND EXISTS (
                SELECT 1 FROM svg_config sc WHERE sc.device_id = d.id
              )
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE device d
            SET device_subtype = 'svg',
                device_category = 'compensation',
                device_type = 'svg'
            WHERE d.device_subtype IS NULL
              AND d.device_type = 'svg'
              AND EXISTS (
                SELECT 1 FROM svg_telemetry st WHERE st.device_id = d.id
              )
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE device
            SET device_subtype = 'capacitor_bank_controller',
                device_category = 'compensation',
                device_type = 'capacitor_bank_controller'
            WHERE device_subtype IS NULL
              AND device_category = 'compensation'
              AND device_type = 'svg'
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE device
            SET device_subtype = 'svg',
                device_category = 'compensation'
            WHERE device_subtype IS NULL
              AND device_type = 'svg'
            """
        )
    )


def downgrade() -> None:
    if _has_index("device", "ix_device_device_subtype"):
        op.drop_index("ix_device_device_subtype", table_name="device")
    if _has_column("device", "device_subtype"):
        op.drop_column("device", "device_subtype")
