"""
设备接口共享模型
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DeviceCreateRequest(BaseModel):
    """智能设备创建请求"""

    name: str = Field(..., description="设备名称")
    sn: str = Field(..., description="设备序列号")
    device_type: str = Field(..., description="设备类型（如 water_meter, solar）")
    location: Optional[str] = Field(None, description="设备位置")
    description: Optional[str] = Field(None, description="设备描述")
    rated_capacity: Optional[float] = Field(None, description="额定容量")


class DeviceUpdateRequest(BaseModel):
    """设备更新请求"""

    name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    rated_capacity: Optional[float] = None


class DeviceDataReportRequest(BaseModel):
    """设备数据上报请求"""

    consumption: float = Field(..., description="消耗量/累计量")
    flow_rate: Optional[float] = Field(None, description="瞬时流量")
    power: Optional[float] = Field(None, description="瞬时功率（电力设备）")
    timestamp: Optional[datetime] = Field(None, description="时间戳")
    voltage: Optional[float] = None
    current: Optional[float] = None
    power_factor: Optional[float] = None
    pressure: Optional[float] = None
    temperature: Optional[float] = None
    supply_temp: Optional[float] = None
    return_temp: Optional[float] = None
    heat_flow: Optional[float] = None
    quality_index: Optional[float] = None
