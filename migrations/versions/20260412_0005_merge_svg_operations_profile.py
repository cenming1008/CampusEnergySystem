"""merge SVG operations profile into svg_asset_profile

Revision ID: 20260412_0005
Revises: 20260412_0004
Create Date: 2026-04-12

说明：
    将原 svg_config 中由运维维护的基础参数并入 svg_asset_profile，
    形成统一的 SVG 运维档案表。保留 svg_telemetry 作为时序表。
"""

from alembic import op
import sqlalchemy as sa


revision = "20260412_0005"
down_revision = "20260412_0004"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    )
    return result.fetchone() is not None


def _has_table(table: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_name = :t"
        ),
        {"t": table},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    columns = (
        ("model_number", sa.String()),
        ("rated_voltage", sa.Float()),
        ("rated_frequency", sa.Float()),
        ("comm_address", sa.String()),
        ("software_version", sa.String()),
        ("hardware_version", sa.String()),
        ("protocol_version", sa.String()),
        ("module_count", sa.Integer()),
        ("single_module_capacity", sa.Float()),
    )

    for name, column_type in columns:
        if not _has_column("svg_asset_profile", name):
            op.add_column("svg_asset_profile", sa.Column(name, column_type, nullable=True))

    if _has_table("svg_config"):
        op.execute(
            sa.text(
                """
                INSERT INTO svg_asset_profile (
                    device_id, model_number, rated_voltage, rated_frequency, comm_address,
                    software_version, hardware_version, protocol_version,
                    module_count, single_module_capacity, created_at, updated_at
                )
                SELECT
                    c.device_id, c.model_number, c.rated_voltage, c.rated_frequency, c.comm_address,
                    c.software_version, c.hardware_version, c.protocol_version,
                    c.module_count, c.single_module_capacity, c.created_at, c.updated_at
                FROM svg_config c
                ON CONFLICT (device_id) DO UPDATE SET
                    model_number = COALESCE(svg_asset_profile.model_number, EXCLUDED.model_number),
                    rated_voltage = COALESCE(svg_asset_profile.rated_voltage, EXCLUDED.rated_voltage),
                    rated_frequency = COALESCE(svg_asset_profile.rated_frequency, EXCLUDED.rated_frequency),
                    comm_address = COALESCE(svg_asset_profile.comm_address, EXCLUDED.comm_address),
                    software_version = COALESCE(svg_asset_profile.software_version, EXCLUDED.software_version),
                    hardware_version = COALESCE(svg_asset_profile.hardware_version, EXCLUDED.hardware_version),
                    protocol_version = COALESCE(svg_asset_profile.protocol_version, EXCLUDED.protocol_version),
                    module_count = COALESCE(svg_asset_profile.module_count, EXCLUDED.module_count),
                    single_module_capacity = COALESCE(svg_asset_profile.single_module_capacity, EXCLUDED.single_module_capacity),
                    updated_at = GREATEST(svg_asset_profile.updated_at, EXCLUDED.updated_at)
                """
            )
        )


def downgrade() -> None:
    for column_name in (
        "single_module_capacity",
        "module_count",
        "protocol_version",
        "hardware_version",
        "software_version",
        "comm_address",
        "rated_frequency",
        "rated_voltage",
        "model_number",
    ):
        if _has_column("svg_asset_profile", column_name):
            op.drop_column("svg_asset_profile", column_name)
