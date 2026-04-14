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


def upgrade() -> None:
    op.add_column("device", sa.Column("device_subtype", sa.String(length=64), nullable=True))
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
    op.drop_index("ix_device_device_subtype", table_name="device")
    op.drop_column("device", "device_subtype")
