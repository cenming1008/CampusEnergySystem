"""prepare compensation subtype migration

Revision ID: 20260414_0006
Revises: 20260412_0005
Create Date: 2026-04-14

说明：
    原始方案计划将历史补偿器类型并入 svg，但后续建模调整为
    “设备类型 + 设备子类型”两级结构，本迁移保留 revision 占位，
    具体数据迁移在后续 revision 中完成，避免破坏旧数据语义。
"""

from alembic import op
import sqlalchemy as sa


revision = "20260414_0006"
down_revision = "20260412_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
