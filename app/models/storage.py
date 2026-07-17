"""储能类设备专属模型。"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class StorageAssetProfile(SQLModel, table=True):
    """储能设备资产、能力与安全边界档案。"""

    __tablename__ = "storage_asset_profile"

    device_id: int = Field(primary_key=True, foreign_key="device.id", description="设备ID")
    rated_energy_kwh: float = Field(description="额定能量 (kWh)")
    rated_power_kw: float = Field(description="PCS 额定功率 (kW)")
    max_charge_power_kw: Optional[float] = Field(default=None, description="最大充电功率 (kW)")
    max_discharge_power_kw: Optional[float] = Field(default=None, description="最大放电功率 (kW)")
    charge_efficiency: float = Field(default=0.95, description="充电效率")
    discharge_efficiency: float = Field(default=0.95, description="放电效率")
    soc_min: float = Field(default=10.0, description="SOC 安全下限 (%)")
    soc_max: float = Field(default=90.0, description="SOC 安全上限 (%)")
    soc_soft_min: float = Field(default=15.0, description="SOC 优化软下限 (%)")
    soc_soft_max: float = Field(default=85.0, description="SOC 优化软上限 (%)")
    rated_ac_voltage: Optional[float] = Field(default=None, description="额定交流电压 (V)")
    rated_dc_voltage: Optional[float] = Field(default=None, description="额定直流电压 (V)")
    battery_type: Optional[str] = Field(default=None, description="电池类型")
    bms_model: Optional[str] = Field(default=None, description="BMS 型号")
    pcs_model: Optional[str] = Field(default=None, description="PCS 型号")
    protocol_version: Optional[str] = Field(default=None, description="协议版本")
    installation_location: Optional[str] = Field(default=None, description="安装位置")
    commission_date: Optional[date] = Field(default=None, description="投运日期")
    data_source: str = Field(default="configured", description="档案数据来源")
    ems_auto_enabled: bool = Field(default=False, description="设备级 EMS 自动控制授权")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")


class StorageTelemetry(SQLModel, table=True):
    """储能系统时序扩展数据（与 EnergyData 同频写入）。"""

    __tablename__ = "storage_telemetry"

    device_id: int = Field(foreign_key="device.id", primary_key=True, description="关联设备ID")
    timestamp: datetime = Field(primary_key=True, description="数据时间戳")

    # 核心状态
    soc: Optional[float] = Field(default=None, description="荷电状态 (%)")
    soh: Optional[float] = Field(default=None, description="健康状态 (%)")

    # 功率（正=充电，负=放电）
    active_power: Optional[float] = Field(default=None, description="有功功率 (kW)，正=充电，负=放电")
    reactive_power: Optional[float] = Field(default=None, description="无功功率 (kVAR)")

    # 直流侧
    dc_voltage: Optional[float] = Field(default=None, description="直流母线电压 (V)")
    dc_current: Optional[float] = Field(default=None, description="直流电流 (A)")

    # 交流侧（三相）
    ac_voltage_a: Optional[float] = Field(default=None, description="A相交流电压 (V)")
    ac_voltage_b: Optional[float] = Field(default=None, description="B相交流电压 (V)")
    ac_voltage_c: Optional[float] = Field(default=None, description="C相交流电压 (V)")
    ac_current_a: Optional[float] = Field(default=None, description="A相交流电流 (A)")
    ac_current_b: Optional[float] = Field(default=None, description="B相交流电流 (A)")
    ac_current_c: Optional[float] = Field(default=None, description="C相交流电流 (A)")
    frequency: Optional[float] = Field(default=None, description="电网频率 (Hz)")

    # 温度
    cell_temp_max: Optional[float] = Field(default=None, description="最高单体温度 (°C)")
    cell_temp_min: Optional[float] = Field(default=None, description="最低单体温度 (°C)")
    cell_temp_avg: Optional[float] = Field(default=None, description="平均单体温度 (°C)")

    # 运行状态
    run_state: Optional[str] = Field(default=None, description="运行状态：idle/charging/discharging/fault/standby")
    control_mode: Optional[str] = Field(default=None, description="控制模式：auto/manual")
    fault_code: Optional[int] = Field(default=None, description="故障码")
    alarm_code: Optional[int] = Field(default=None, description="告警码")

    # 能量统计
    charge_energy_today: Optional[float] = Field(default=None, description="今日充电量 (kWh)")
    discharge_energy_today: Optional[float] = Field(default=None, description="今日放电量 (kWh)")
    charge_energy_total: Optional[float] = Field(default=None, description="累计充电量 (kWh)")
    discharge_energy_total: Optional[float] = Field(default=None, description="累计放电量 (kWh)")
    cycle_count: Optional[int] = Field(default=None, description="循环次数")

    # 控制闭环扩展
    target_active_power: Optional[float] = Field(default=None, description="目标有功功率 (kW)")
    available_charge_power: Optional[float] = Field(default=None, description="可充电功率 (kW)")
    available_discharge_power: Optional[float] = Field(default=None, description="可放电功率 (kW)")
    bms_status: Optional[str] = Field(default=None, description="BMS 状态")
    pcs_status: Optional[str] = Field(default=None, description="PCS 状态")
    grid_status: Optional[str] = Field(default=None, description="并网状态")
    command_source: Optional[str] = Field(default=None, description="当前功率命令来源")
    data_source: str = Field(default="telemetry", description="遥测数据来源")
    simulation_run_id: Optional[str] = Field(default=None, index=True, description="模拟运行标识")


class StorageDispatchPlan(SQLModel, table=True):
    """储能日前调度的单个 15 分钟计划点。"""

    __tablename__ = "storage_dispatch_plan"
    __table_args__ = (
        UniqueConstraint(
            "device_id",
            "dispatch_date",
            "slot_index",
            name="uq_storage_dispatch_device_date_slot",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: int = Field(foreign_key="device.id", description="设备ID")
    dispatch_date: date = Field(description="调度日期")
    slot_index: int = Field(description="15 分钟时段序号，服务层校验 0-95")
    interval_minutes: int = Field(default=15, description="时段长度（分钟）")
    target_active_power: float = Field(description="计划目标功率 (kW)，正充负放")
    forecast_load_power: Optional[float] = Field(default=None, description="预测负荷功率 (kW)")
    forecast_pv_power: Optional[float] = Field(default=None, description="预测光伏功率 (kW)")
    tariff_price: Optional[float] = Field(default=None, description="分时电价")
    expected_soc: Optional[float] = Field(default=None, description="预计 SOC (%)")
    strategy: str = Field(default="day_ahead", description="策略类型")
    strategy_version: str = Field(default="v1", description="策略版本")
    solver_status: str = Field(default="pending", description="求解状态")
    is_valid: bool = Field(default=True, description="计划是否有效")
    failure_reason: Optional[str] = Field(default=None, description="失败或回退原因")
    generated_at: datetime = Field(default_factory=datetime.now, description="计划生成时间")
    data_source: str = Field(default="calculated", description="计划来源：calculated/simulated/real")
    simulation_run_id: Optional[str] = Field(default=None, index=True, description="模拟运行标识")
