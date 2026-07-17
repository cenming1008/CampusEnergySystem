"""储能设备嵌套接口契约。"""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from sqlmodel import SQLModel


class StorageAssetProfileUpdate(SQLModel):
    rated_energy_kwh: float
    rated_power_kw: float
    max_charge_power_kw: Optional[float] = None
    max_discharge_power_kw: Optional[float] = None
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.95
    soc_min: float = 10.0
    soc_max: float = 90.0
    soc_soft_min: float = 15.0
    soc_soft_max: float = 85.0
    rated_ac_voltage: Optional[float] = None
    rated_dc_voltage: Optional[float] = None
    battery_type: Optional[str] = None
    bms_model: Optional[str] = None
    pcs_model: Optional[str] = None
    protocol_version: Optional[str] = None
    installation_location: Optional[str] = None
    commission_date: Optional[date] = None
    data_source: str = "configured"
    ems_auto_enabled: bool = False


class StorageControlRequest(SQLModel):
    command: Literal["set_active_power", "set_control_mode", "stop"]
    target_active_power: Optional[float] = None
    control_mode: Optional[Literal["auto", "manual"]] = None
    source: Literal["manual", "rule", "day_ahead"] = "manual"
    reason: Optional[str] = None


class StorageControlResponse(SQLModel):
    accepted: bool
    status: str
    command_id: str
    message: str


class StorageSimulationControlRequest(SQLModel):
    action: Literal["set_scenario", "set_speed", "inject_fault", "clear_fault"]
    scenario: Optional[
        Literal[
            "sunny_workday",
            "cloudy_workday",
            "weekend_low_load",
            "pv_surplus",
            "evening_peak",
        ]
    ] = None
    speed: Optional[Literal[1, 10, 60, 288]] = None
    fault: Optional[
        Literal[
            "low_soc",
            "overtemperature",
            "pcs_fault",
            "communication_loss",
            "pv_drop",
        ]
    ] = None
