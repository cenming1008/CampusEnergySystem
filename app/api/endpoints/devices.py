"""
设备管理API端点 - 统一的设备和数据管理接口
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import Device, EnergyData
from app.services.device_service import DeviceService
from app.services.mqtt_publisher import publish_control_command

router = APIRouter()


# ==================== 请求/响应模型 ====================

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
    
    # 电力专用字段
    voltage: Optional[float] = None
    current: Optional[float] = None
    power_factor: Optional[float] = None
    
    # 水/气专用字段
    pressure: Optional[float] = None
    temperature: Optional[float] = None
    
    # 热力专用字段
    supply_temp: Optional[float] = None
    return_temp: Optional[float] = None
    heat_flow: Optional[float] = None
    
    # 质量指标
    quality_index: Optional[float] = None


# ==================== 设备管理端点 ====================

@router.get("/", response_model=List[Device])
def get_devices(
    energy_type: Optional[str] = Query(None, description="按能源类型筛选"),
    category: Optional[str] = Query(None, description="按设备类别筛选"),
    is_active: Optional[bool] = Query(None, description="按状态筛选"),
    session: Session = Depends(get_session)
):
    """
    获取设备列表
    
    支持多种筛选条件：
    - energy_type: 能源类型（electricity, water, gas, heat, cooling, steam）
    - category: 设备类别（load, solar, water_meter, etc）
    - is_active: 是否启用
    """
    devices = DeviceService.get_all_devices(
        session,
        energy_type=energy_type,
        category=category,
        is_active=is_active
    )
    return devices


@router.get("/types")
def get_device_types():
    """
    获取所有支持的设备类型
    
    返回设备类型注册表，包含每种设备的配置信息
    """
    return success_response(data=DeviceService.get_device_types())


@router.get("/types/{device_type}")
def get_device_type_info(device_type: str):
    """获取指定设备类型的详细信息"""
    info = DeviceService.get_device_type_info(device_type)
    if not info:
        raise HTTPException(status_code=404, detail=f"设备类型不存在: {device_type}")
    return success_response(data=info)


@router.post("/", response_model=Device)
def create_device_smart(
    req: DeviceCreateRequest,
    session: Session = Depends(get_session)
):
    """
    智能创建设备
    
    根据设备类型自动配置能源类型、设备类别、单位等信息。
    
    示例:
    ```json
    {
      "name": "1号水表",
      "sn": "WATER001",
      "device_type": "water_meter",
      "location": "A栋1层"
    }
    ```
    
    系统会自动设置:
    - energy_type: "water"
    - device_category: "water_meter"
    - unit: "m³/h"
    - rated_capacity: 50.0 (默认值)
    """
    try:
        device = DeviceService.create_device_smart(
            session=session,
            name=req.name,
            sn=req.sn,
            device_type=req.device_type,
            location=req.location,
            description=req.description,
            rated_capacity=req.rated_capacity
        )
        return device
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建设备失败: {str(e)}")


@router.post("/legacy", response_model=Device)
def create_device_legacy(
    device: Device,
    session: Session = Depends(get_session)
):
    """
    创建设备（传统方式）
    
    保留此端点用于向后兼容。
    建议使用 POST /devices/ 端点（智能创建）。
    """
    return DeviceService.create_device(session, device)


@router.get("/{device_id}", response_model=Device)
def get_device(
    device_id: int,
    session: Session = Depends(get_session)
):
    """获取设备详情"""
    return DeviceService.get_device_by_id(session, device_id)


@router.put("/{device_id}", response_model=Device)
def update_device(
    device_id: int,
    req: DeviceUpdateRequest,
    session: Session = Depends(get_session)
):
    """更新设备信息"""
    try:
        return DeviceService.update_device(
            session,
            device_id,
            name=req.name,
            location=req.location,
            description=req.description,
            rated_capacity=req.rated_capacity
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新设备失败: {str(e)}")


@router.delete("/{device_id}")
def delete_device(
    device_id: int,
    session: Session = Depends(get_session)
):
    """删除设备"""
    device = DeviceService.get_device_by_id(session, device_id)
    DeviceService.delete_device(session, device_id)
    return success_response(message=f"设备 {device.name} 已删除")


@router.post("/{device_id}/toggle")
def toggle_device_status(
    device_id: int,
    active: bool,
    session: Session = Depends(get_session)
):
    """切换设备启停状态"""
    device = DeviceService.toggle_device_status(session, device_id, active)
    
    # 发送MQTT控制指令
    action_code = "start" if active else "stop"
    publish_control_command(device.id, action_code)
    
    return device


# ==================== 设备数据管理端点 ====================

@router.post("/{device_id}/data", response_model=EnergyData)
def report_device_data(
    device_id: int,
    req: DeviceDataReportRequest,
    session: Session = Depends(get_session)
):
    """
    设备数据上报（统一接口）
    
    所有类型的设备都使用这个接口上报数据。
    系统会根据设备类型自动处理数据字段。
    
    示例 - 电力设备:
    ```json
    {
      "consumption": 100.5,
      "power": 50.2,
      "voltage": 220,
      "current": 15.5
    }
    ```
    
    示例 - 水表:
    ```json
    {
      "consumption": 10.5,
      "flow_rate": 2.3,
      "pressure": 0.3,
      "temperature": 18.5
    }
    ```
    """
    try:
        # 构建数据字典
        data = req.model_dump(exclude_none=True)
        
        energy_data = DeviceService.report_device_data(
            session=session,
            device_id=device_id,
            data=data,
            timestamp=req.timestamp
        )
        
        return energy_data
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据上报失败: {str(e)}")


@router.get("/{device_id}/data", response_model=List[EnergyData])
def get_device_data(
    device_id: int,
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(1000, ge=1, le=10000, description="返回条数限制"),
    session: Session = Depends(get_session)
):
    """
    查询设备数据
    
    获取指定设备的历史数据，支持时间范围筛选。
    """
    try:
        return DeviceService.get_device_data(
            session=session,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询数据失败: {str(e)}")


@router.get("/{device_id}/statistics")
def get_device_statistics(
    device_id: int,
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间"),
    period_type: str = Query("day", description="统计周期: hour/day/month/year"),
    session: Session = Depends(get_session)
):
    """
    获取设备统计数据
    
    统计指定时间段内的总消耗、平均值、峰值等。
    """
    try:
        stats = DeviceService.get_device_statistics(
            session=session,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            period_type=period_type
        )
        return success_response(data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"统计数据失败: {str(e)}")