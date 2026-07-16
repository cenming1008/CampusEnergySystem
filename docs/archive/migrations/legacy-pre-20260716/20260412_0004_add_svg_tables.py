"""add SVG device tables

Revision ID: 20260412_0004
Revises: 20260412_0003
Create Date: 2026-04-12

说明：
    新增三张 SVG（静止无功发生器）专属数据表：
    - svg_config: SVG 静态设备参数（型号、版本、模块参数等）
    - svg_telemetry: SVG 时序扩展数据（三相量、状态位、温度、故障码等）
    - svg_asset_profile: SVG 资产档案（资产管理、现场安装、管理责任、平台建模）
"""

import sqlalchemy as sa
from alembic import op

revision = "20260412_0004"
down_revision = "20260412_0003"
branch_labels = None
depends_on = None


def _has_table(table: str) -> bool:
    """检查表是否已存在，防止重复执行迁移时报错。"""
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
    # ── svg_config ─────────────────────────────────────────────────────────
    if not _has_table("svg_config"):
        op.create_table(
            "svg_config",
            sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
            sa.Column("device_id", sa.Integer(), nullable=False),
            sa.Column("model_number", sa.String(), nullable=True, comment="设备型号"),
            sa.Column("rated_voltage", sa.Float(), nullable=True, comment="额定电压 (V)"),
            sa.Column("rated_frequency", sa.Float(), nullable=True, comment="额定频率 (Hz)"),
            sa.Column("comm_address", sa.String(), nullable=True, comment="通信地址"),
            sa.Column("software_version", sa.String(), nullable=True, comment="软件版本"),
            sa.Column("hardware_version", sa.String(), nullable=True, comment="硬件版本"),
            sa.Column("protocol_version", sa.String(), nullable=True, comment="协议版本"),
            sa.Column("module_count", sa.Integer(), nullable=True, comment="模块数量"),
            sa.Column("single_module_capacity", sa.Float(), nullable=True, comment="单模块容量 (kVAR)"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["device_id"], ["device.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("device_id"),
        )
        op.create_index("ix_svg_config_device_id", "svg_config", ["device_id"])

    # ── svg_telemetry ───────────────────────────────────────────────────────
    if not _has_table("svg_telemetry"):
        op.create_table(
            "svg_telemetry",
            sa.Column("device_id", sa.Integer(), nullable=False),
            sa.Column("timestamp", sa.DateTime(), nullable=False),
            # 三相电压
            sa.Column("voltage_a", sa.Float(), nullable=True, comment="A相电压 (V)"),
            sa.Column("voltage_b", sa.Float(), nullable=True, comment="B相电压 (V)"),
            sa.Column("voltage_c", sa.Float(), nullable=True, comment="C相电压 (V)"),
            # 三相电流
            sa.Column("current_a", sa.Float(), nullable=True, comment="A相电流 (A)"),
            sa.Column("current_b", sa.Float(), nullable=True, comment="B相电流 (A)"),
            sa.Column("current_c", sa.Float(), nullable=True, comment="C相电流 (A)"),
            sa.Column("frequency", sa.Float(), nullable=True, comment="频率 (Hz)"),
            sa.Column("svg_reactive_output", sa.Float(), nullable=True, comment="SVG当前输出无功 (kVAR)"),
            sa.Column("capacity_utilization", sa.Float(), nullable=True, comment="容量利用率 (%)"),
            sa.Column("output_direction", sa.String(), nullable=True, comment="输出方向：inductive/capacitive"),
            # 状态位
            sa.Column("run_status", sa.Boolean(), nullable=True, comment="运行状态"),
            sa.Column("stop_status", sa.Boolean(), nullable=True, comment="停机状态"),
            sa.Column("auto_mode", sa.Boolean(), nullable=True, comment="自动模式"),
            sa.Column("local_mode", sa.Boolean(), nullable=True, comment="本地模式"),
            sa.Column("breaker_status", sa.Boolean(), nullable=True, comment="断路器状态"),
            sa.Column("module_status", sa.Boolean(), nullable=True, comment="模块状态"),
            sa.Column("fan_status", sa.Boolean(), nullable=True, comment="风机状态"),
            sa.Column("comm_status", sa.Boolean(), nullable=True, comment="通信状态"),
            # 故障位
            sa.Column("overvoltage_fault", sa.Boolean(), nullable=True, comment="过压故障"),
            sa.Column("undervoltage_fault", sa.Boolean(), nullable=True, comment="欠压故障"),
            sa.Column("overcurrent_fault", sa.Boolean(), nullable=True, comment="过流故障"),
            sa.Column("overtemp_fault", sa.Boolean(), nullable=True, comment="过温故障"),
            sa.Column("module_fault", sa.Boolean(), nullable=True, comment="模块故障"),
            sa.Column("fan_fault", sa.Boolean(), nullable=True, comment="风机故障"),
            sa.Column("comm_fault", sa.Boolean(), nullable=True, comment="通信故障"),
            sa.Column("current_fault_code", sa.String(), nullable=True, comment="当前故障代码"),
            sa.Column("current_alarm_code", sa.String(), nullable=True, comment="当前告警代码"),
            # 温度和内部量
            sa.Column("cabinet_temp", sa.Float(), nullable=True, comment="柜内温度 (°C)"),
            sa.Column("module_temp", sa.Float(), nullable=True, comment="模块温度 (°C)"),
            sa.Column("igbt_temp", sa.Float(), nullable=True, comment="IGBT温度 (°C)"),
            sa.Column("dc_bus_voltage", sa.Float(), nullable=True, comment="直流母线电压 (V)"),
            sa.Column("heatsink_temp", sa.Float(), nullable=True, comment="散热器温度 (°C)"),
            sa.ForeignKeyConstraint(["device_id"], ["device.id"]),
            sa.PrimaryKeyConstraint("device_id", "timestamp"),
        )

    # ── svg_asset_profile ───────────────────────────────────────────────────
    if not _has_table("svg_asset_profile"):
        op.create_table(
            "svg_asset_profile",
            sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
            sa.Column("device_id", sa.Integer(), nullable=False),
            # 资产管理类
            sa.Column("device_label_zh", sa.String(), nullable=True, comment="设备中文标签"),
            sa.Column("asset_number", sa.String(), nullable=True, comment="资产编号"),
            sa.Column("fixed_asset_code", sa.String(), nullable=True, comment="固定资产编码"),
            sa.Column("qr_code_number", sa.String(), nullable=True, comment="设备二维码编号"),
            sa.Column("asset_group", sa.String(), nullable=True, comment="所属资产组"),
            # 现场安装类
            sa.Column("distribution_room", sa.String(), nullable=True, comment="所属配电室"),
            sa.Column("distribution_cabinet", sa.String(), nullable=True, comment="所属配电柜"),
            sa.Column("circuit", sa.String(), nullable=True, comment="所属回路"),
            sa.Column("area", sa.String(), nullable=True, comment="所属区域"),
            sa.Column("building", sa.String(), nullable=True, comment="所属楼栋"),
            sa.Column("install_date", sa.Date(), nullable=True, comment="安装日期"),
            sa.Column("commission_date", sa.Date(), nullable=True, comment="投运日期"),
            sa.Column("field_number", sa.String(), nullable=True, comment="现场编号"),
            # 管理责任类
            sa.Column("om_responsible", sa.String(), nullable=True, comment="运维负责人"),
            sa.Column("inspection_responsible", sa.String(), nullable=True, comment="巡检负责人"),
            sa.Column("department", sa.String(), nullable=True, comment="所属部门"),
            sa.Column("management_unit", sa.String(), nullable=True, comment="管理单位"),
            sa.Column("contact_phone", sa.String(), nullable=True, comment="联系电话"),
            sa.Column("warranty_expiry", sa.Date(), nullable=True, comment="保修到期时间"),
            sa.Column("maintenance_cycle_days", sa.Integer(), nullable=True, comment="维护周期（天）"),
            # 平台建模类
            sa.Column("device_group", sa.String(), nullable=True, comment="设备分组"),
            sa.Column("device_tree_level", sa.String(), nullable=True, comment="设备树层级"),
            sa.Column("monitor_screen_position", sa.String(), nullable=True, comment="监控画面位置"),
            sa.Column("alarm_policy", sa.String(), nullable=True, comment="告警归属策略"),
            sa.Column("device_alias", sa.String(), nullable=True, comment="设备别名"),
            sa.Column("display_name", sa.String(), nullable=True, comment="上位机显示名称"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["device_id"], ["device.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("device_id"),
        )
        op.create_index("ix_svg_asset_profile_device_id", "svg_asset_profile", ["device_id"])


def downgrade() -> None:
    op.drop_table("svg_asset_profile")
    op.drop_table("svg_telemetry")
    op.drop_table("svg_config")
