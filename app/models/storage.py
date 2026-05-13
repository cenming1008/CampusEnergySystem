"""储能类设备专属模型。"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


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
