"""
设备接口共享模型
"""

from __future__ import annotations

from datetime import datetime
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class SVGOperationsProfilePayload(BaseModel):
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


class DeviceCreateRequest(BaseModel):
    """智能设备创建请求"""

    name: str = Field(..., description="设备名称")
    sn: str = Field(..., description="设备序列号")
    device_type: str = Field(..., description="设备类型；决定设备对象语义、计量语义和默认能源类别")
    location: Optional[str] = Field(None, description="设备位置")
    description: Optional[str] = Field(None, description="设备描述")
    rated_capacity: Optional[float] = Field(None, description="额定容量")
    svg_operations: Optional[SVGOperationsProfilePayload] = Field(None, description="SVG 运维档案")


class DeviceUpdateRequest(BaseModel):
    """设备更新请求"""

    name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    rated_capacity: Optional[float] = None
    svg_operations: Optional[SVGOperationsProfilePayload] = None


class DeviceDataReportRequest(BaseModel):
    """设备数据上报请求"""

    consumption: float = Field(..., description="公共层字段：累计量/累计读数")
    flow_rate: Optional[float] = Field(None, description="公共层字段：瞬时量（流量/功率/负荷）")
    power: Optional[float] = Field(None, description="兼容别名：电力设备瞬时功率，入库会归一到 flow_rate")
    timestamp: Optional[datetime] = Field(None, description="时间戳")
    voltage: Optional[float] = None
    current: Optional[float] = None
    power_factor: Optional[float] = None
    pressure: Optional[float] = None
    temperature: Optional[float] = None
    supply_temp: Optional[float] = None
    return_temp: Optional[float] = None
    heat_flow: Optional[float] = Field(None, description="热力专属字段；兼容映射到公共瞬时字段 flow_rate")
    quality_index: Optional[float] = None
