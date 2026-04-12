"""add reactive_power column to energydata

Revision ID: 20260412_0003
Revises: 20260325_0002
Create Date: 2026-04-12

说明：
    为 EnergyData 表新增 reactive_power（无功功率，kVAR）字段，
    支持无功功率补偿器（SVG/SVC/电容补偿柜）等设备的无功数据接入。
    正值表示感性负载吸收，负值表示容性补偿输出。
"""

import sqlalchemy as sa
from alembic import op

revision = "20260412_0003"
down_revision = "20260325_0002"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    """检查列是否已存在，防止重复执行迁移时报错。"""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    if not _has_column("energydata", "reactive_power"):
        op.add_column(
            "energydata",
            sa.Column(
                "reactive_power",
                sa.Float(),
                nullable=True,
                comment="无功功率(kVAR)，正值=感性，负值=容性补偿输出",
            ),
        )


def downgrade() -> None:
    op.drop_column("energydata", "reactive_power")
