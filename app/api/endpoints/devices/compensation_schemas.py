"""
补偿类设备共享 schema。

仅承载补偿设备族公共契约：
- SVG 运维档案
- SVG 扩展遥测
- 电容补偿控制器扩展遥测
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict


class SVGOperationsProfilePayload(BaseModel):
    """SVG 运维档案写入载荷。"""

    model_number: Optional[str] = None
    rated_voltage: Optional[float] = None
    rated_frequency: Optional[float] = None
    comm_address: Optional[str] = None
    software_version: Optional[str] = None
    hardware_version: Optional[str] = None
    protocol_version: Optional[str] = None
    module_count: Optional[int] = None
    single_module_capacity: Optional[float] = None
    device_label_zh: Optional[str] = None
    asset_number: Optional[str] = None
    fixed_asset_code: Optional[str] = None
    qr_code_number: Optional[str] = None
    asset_group: Optional[str] = None
    distribution_room: Optional[str] = None
    distribution_cabinet: Optional[str] = None
    circuit: Optional[str] = None
    area: Optional[str] = None
    building: Optional[str] = None
    install_date: Optional[date] = None
    commission_date: Optional[date] = None
    field_number: Optional[str] = None
    om_responsible: Optional[str] = None
    inspection_responsible: Optional[str] = None
    department: Optional[str] = None
    management_unit: Optional[str] = None
    contact_phone: Optional[str] = None
    warranty_expiry: Optional[date] = None
    maintenance_cycle_days: Optional[int] = None
    device_group: Optional[str] = None
    device_tree_level: Optional[str] = None
    monitor_screen_position: Optional[str] = None
    alarm_policy: Optional[str] = None
    device_alias: Optional[str] = None
    display_name: Optional[str] = None


class SVGOperationsProfileUpdate(BaseModel):
    """SVG 运维档案更新载荷。"""

    model_number: Optional[str] = None
    rated_voltage: Optional[float] = None
    rated_frequency: Optional[float] = None
    comm_address: Optional[str] = None
    software_version: Optional[str] = None
    hardware_version: Optional[str] = None
    protocol_version: Optional[str] = None
    module_count: Optional[int] = None
    single_module_capacity: Optional[float] = None
    device_label_zh: Optional[str] = None
    asset_number: Optional[str] = None
    fixed_asset_code: Optional[str] = None
    qr_code_number: Optional[str] = None
    asset_group: Optional[str] = None
    distribution_room: Optional[str] = None
    distribution_cabinet: Optional[str] = None
    circuit: Optional[str] = None
    area: Optional[str] = None
    building: Optional[str] = None
    install_date: Optional[str] = None
    commission_date: Optional[str] = None
    field_number: Optional[str] = None
    om_responsible: Optional[str] = None
    inspection_responsible: Optional[str] = None
    department: Optional[str] = None
    management_unit: Optional[str] = None
    contact_phone: Optional[str] = None
    warranty_expiry: Optional[str] = None
    maintenance_cycle_days: Optional[int] = None
    device_group: Optional[str] = None
    device_tree_level: Optional[str] = None
    monitor_screen_position: Optional[str] = None
    alarm_policy: Optional[str] = None
    device_alias: Optional[str] = None
    display_name: Optional[str] = None


class SVGOperationsProfileResponse(BaseModel):
    """SVG 运维档案响应模型。"""

    id: Optional[int]
    device_id: int
    model_number: Optional[str]
    rated_voltage: Optional[float]
    rated_frequency: Optional[float]
    comm_address: Optional[str]
    software_version: Optional[str]
    hardware_version: Optional[str]
    protocol_version: Optional[str]
    module_count: Optional[int]
    single_module_capacity: Optional[float]
    device_label_zh: Optional[str]
    asset_number: Optional[str]
    fixed_asset_code: Optional[str]
    qr_code_number: Optional[str]
    asset_group: Optional[str]
    distribution_room: Optional[str]
    distribution_cabinet: Optional[str]
    circuit: Optional[str]
    area: Optional[str]
    building: Optional[str]
    install_date: Optional[str]
    commission_date: Optional[str]
    field_number: Optional[str]
    om_responsible: Optional[str]
    inspection_responsible: Optional[str]
    department: Optional[str]
    management_unit: Optional[str]
    contact_phone: Optional[str]
    warranty_expiry: Optional[str]
    maintenance_cycle_days: Optional[int]
    device_group: Optional[str]
    device_tree_level: Optional[str]
    monitor_screen_position: Optional[str]
    alarm_policy: Optional[str]
    device_alias: Optional[str]
    display_name: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class SVGTelemetryResponse(BaseModel):
    """SVG 扩展遥测响应模型。"""

    device_id: int
    timestamp: datetime
    voltage_a: Optional[float]
    voltage_b: Optional[float]
    voltage_c: Optional[float]
    current_a: Optional[float]
    current_b: Optional[float]
    current_c: Optional[float]
    frequency: Optional[float]
    svg_reactive_output: Optional[float]
    capacity_utilization: Optional[float]
    output_direction: Optional[str]
    run_status: Optional[bool]
    stop_status: Optional[bool]
    auto_mode: Optional[bool]
    local_mode: Optional[bool]
    breaker_status: Optional[bool]
    module_status: Optional[bool]
    fan_status: Optional[bool]
    comm_status: Optional[bool]
    overvoltage_fault: Optional[bool]
    undervoltage_fault: Optional[bool]
    overcurrent_fault: Optional[bool]
    overtemp_fault: Optional[bool]
    module_fault: Optional[bool]
    fan_fault: Optional[bool]
    comm_fault: Optional[bool]
    current_fault_code: Optional[str]
    current_alarm_code: Optional[str]
    cabinet_temp: Optional[float]
    module_temp: Optional[float]
    igbt_temp: Optional[float]
    dc_bus_voltage: Optional[float]
    heatsink_temp: Optional[float]

    model_config = ConfigDict(from_attributes=True)


class CapacitorBankTelemetryResponse(BaseModel):
    """电容补偿控制器扩展遥测响应模型。"""

    device_id: int
    timestamp: datetime
    voltage_a: Optional[float] = None
    voltage_b: Optional[float] = None
    voltage_c: Optional[float] = None
    current_a: Optional[float] = None
    current_b: Optional[float] = None
    current_c: Optional[float] = None
    power_factor_a: Optional[float] = None
    power_factor_b: Optional[float] = None
    power_factor_c: Optional[float] = None
    active_power_a: Optional[float] = None
    active_power_b: Optional[float] = None
    active_power_c: Optional[float] = None
    reactive_power_a: Optional[float] = None
    reactive_power_b: Optional[float] = None
    reactive_power_c: Optional[float] = None
    apparent_power_a: Optional[float] = None
    apparent_power_b: Optional[float] = None
    apparent_power_c: Optional[float] = None
    voltage_thd_a: Optional[float] = None
    voltage_thd_b: Optional[float] = None
    voltage_thd_c: Optional[float] = None
    current_harmonic_a: Optional[float] = None
    current_harmonic_b: Optional[float] = None
    current_harmonic_c: Optional[float] = None
    frequency: Optional[float] = None
    temperature: Optional[float] = None
    leading_a: Optional[bool] = None
    leading_b: Optional[bool] = None
    leading_c: Optional[bool] = None
    undercurrent_a: Optional[bool] = None
    undercurrent_b: Optional[bool] = None
    undercurrent_c: Optional[bool] = None
    overvoltage_alarm_a: Optional[bool] = None
    overvoltage_alarm_b: Optional[bool] = None
    overvoltage_alarm_c: Optional[bool] = None
    voltage_thd_alarm_a: Optional[bool] = None
    voltage_thd_alarm_b: Optional[bool] = None
    voltage_thd_alarm_c: Optional[bool] = None
    current_thd_alarm_a: Optional[bool] = None
    current_thd_alarm_b: Optional[bool] = None
    current_thd_alarm_c: Optional[bool] = None
    temp_alarm: Optional[bool] = None
    circuit_state_phase_a: Optional[int] = None
    circuit_state_phase_b: Optional[int] = None
    circuit_state_phase_c: Optional[int] = None
    circuit_state_common_1: Optional[int] = None
    circuit_state_common_2: Optional[int] = None
    circuit_state_common_3: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class CapacitorBankControlCapabilitiesResponse(BaseModel):
    supports_read: bool
    supports_write: bool
    supports_remote_control: bool
    write_status_message: str
    remote_control_status_message: str
    protocol_version: str
    command_message_type: str
    receipt_message_type: str
    control_topic_template: str
    receipt_topic: str
    receipt_timeout_seconds: int
    supported_results: list[str]


class CapacitorBankControlWriteRequest(BaseModel):
    parameter_key: str
    target_value: Union[str, int, float, bool]
    reason: Optional[str] = None


class CapacitorBankControlWriteResponse(BaseModel):
    accepted: bool
    status: str
    message: str
    command_id: Optional[str] = None


class CapacitorBankRemoteCommandRequest(BaseModel):
    action: str
    manual_mode: Optional[str] = None
    phase: Optional[str] = None
    switch_action: Optional[str] = None
    reason: Optional[str] = None


class CapacitorBankRemoteCommandResponse(BaseModel):
    accepted: bool
    status: str
    message: str
    command_id: Optional[str] = None


class CapacitorBankControlProfileResponse(BaseModel):
    """电容补偿控制器控制台只读参数档案。"""

    device_id: int
    switch_on_power_factor: Optional[float] = None
    switch_off_power_factor: Optional[float] = None
    switch_on_delay_seconds: Optional[int] = None
    switch_off_delay_seconds: Optional[int] = None
    common_output_circuit_count: Optional[int] = None
    split_output_circuit_count: Optional[int] = None
    common_capacity_code: Optional[str] = None
    split_capacity_code: Optional[str] = None
    common_step_capacity_kvar: Optional[float] = None
    split_step_capacity_kvar: Optional[float] = None
    ct_primary_current: Optional[int] = None
    overvoltage_threshold: Optional[float] = None
    voltage_harmonic_threshold: Optional[float] = None
    current_harmonic_threshold: Optional[float] = None
    temperature_upper_limit: Optional[float] = None
    alarm_drive_event: Optional[str] = None
    baud_rate: Optional[int] = None
    terminal_assignment_scheme: Optional[str] = None
    current_polarity_identification_enabled: Optional[bool] = None
    source: Optional[str] = None
    snapshot_timestamp: Optional[datetime] = None
    source_status: str
    is_stale: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    capabilities: CapacitorBankControlCapabilitiesResponse


__all__ = [
    "SVGOperationsProfilePayload",
    "SVGOperationsProfileUpdate",
    "SVGOperationsProfileResponse",
    "SVGTelemetryResponse",
    "CapacitorBankTelemetryResponse",
    "CapacitorBankControlCapabilitiesResponse",
    "CapacitorBankControlWriteRequest",
    "CapacitorBankControlWriteResponse",
    "CapacitorBankRemoteCommandRequest",
    "CapacitorBankRemoteCommandResponse",
    "CapacitorBankControlProfileResponse",
]
