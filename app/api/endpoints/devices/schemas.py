"""
设备域通用 schema。

仅放设备域跨子模块复用的请求模型；
补偿类专属 schema 统一放在 `compensation_schemas.py`。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .compensation_schemas import SVGOperationsProfilePayload


class DeviceCreateRequest(BaseModel):
    """设备主档创建请求。"""

    name: str = Field(..., description="设备名称")
    sn: str = Field(..., description="设备序列号")
    device_type: str = Field(..., description="设备类型（业务大类或兼容旧类型键）")
    device_subtype: Optional[str] = Field(None, description="设备子类型（如 svg / capacitor_bank_controller）")
    location: Optional[str] = Field(None, description="设备位置")
    description: Optional[str] = Field(None, description="设备描述")
    rated_capacity: Optional[float] = Field(None, description="额定容量")
    svg_operations: Optional[SVGOperationsProfilePayload] = Field(None, description="SVG 运维档案")


class DeviceUpdateRequest(BaseModel):
    """设备主档更新请求。"""

    device_type: Optional[str] = None
    device_subtype: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    rated_capacity: Optional[float] = None
    svg_operations: Optional[SVGOperationsProfilePayload] = None


class DeviceDataReportRequest(BaseModel):
    """设备通用数据上报请求。"""

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
