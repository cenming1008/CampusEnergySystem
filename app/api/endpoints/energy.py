"""
多能源管理 API 端点
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import (
    EnergyData, CarbonEmission, Device,
    EnergyType, DeviceCategory
)
from app.services.energy_service import EnergyService

router = APIRouter()


# ==================== 请求/响应模型 ====================

class EnergyDataCreate(BaseModel):
    """能源数据创建模型"""
    device_id: int
    energy_type: str
    consumption: float
    flow_rate: Optional[float] = None
    timestamp: Optional[datetime] = None
    
    # 电力专用
    voltage: Optional[float] = None
    current: Optional[float] = None
    power_factor: Optional[float] = None
    
    # 水/气专用
    pressure: Optional[float] = None
    temperature: Optional[float] = None
    
    # 热力专用
    supply_temp: Optional[float] = None
    return_temp: Optional[float] = None
    heat_flow: Optional[float] = None


class CarbonSummaryResponse(BaseModel):
    """碳排放汇总响应"""
    total_carbon: float
    by_energy_type: dict


class EnergyStatisticsResponse(BaseModel):
    """能源统计响应"""
    total_consumption: float
    avg_consumption: float
    avg_flow_rate: float
    peak_flow_rate: float
    data_count: int


# ==================== API 端点 ====================

@router.post("/data", response_model=EnergyData)
def save_energy_data(
    data: EnergyDataCreate,
    session: Session = Depends(get_session)
):
    """
    保存能源数据
    
    支持多种能源类型：电、水、气、热、冷等
    """
    try:
        # 提取可选字段
        optional_fields = {}
        if data.voltage is not None:
            optional_fields["voltage"] = data.voltage
        if data.current is not None:
            optional_fields["current"] = data.current
        if data.power_factor is not None:
            optional_fields["power_factor"] = data.power_factor
        if data.pressure is not None:
            optional_fields["pressure"] = data.pressure
        if data.temperature is not None:
            optional_fields["temperature"] = data.temperature
        if data.supply_temp is not None:
            optional_fields["supply_temp"] = data.supply_temp
        if data.return_temp is not None:
            optional_fields["return_temp"] = data.return_temp
        if data.heat_flow is not None:
            optional_fields["heat_flow"] = data.heat_flow
        
        energy_data = EnergyService.save_energy_data(
            session=session,
            device_id=data.device_id,
            energy_type=data.energy_type,
            consumption=data.consumption,
            flow_rate=data.flow_rate,
            timestamp=data.timestamp,
            **optional_fields
        )
        
        return energy_data
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存能源数据失败: {str(e)}")


@router.get("/data/{device_id}", response_model=List[EnergyData])
def get_energy_data(
    device_id: int,
    energy_type: Optional[str] = Query(None, description="能源类型"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(1000, ge=1, le=10000, description="返回条数限制"),
    session: Session = Depends(get_session)
):
    """
    查询设备能源数据
    
    可以按能源类型、时间范围筛选
    """
    results = EnergyService.get_energy_data(
        session=session,
        device_id=device_id,
        energy_type=energy_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return results


@router.get("/carbon/emissions", response_model=List[CarbonEmission])
def get_carbon_emissions(
    device_id: Optional[int] = Query(None, description="设备ID，不传则查询所有"),
    energy_type: Optional[str] = Query(None, description="能源类型"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    session: Session = Depends(get_session)
):
    """
    查询碳排放数据
    
    支持按设备、能源类型、时间范围查询
    """
    results = EnergyService.get_carbon_emissions(
        session=session,
        device_id=device_id,
        energy_type=energy_type,
        start_time=start_time,
        end_time=end_time
    )
    
    return results


@router.get("/carbon/summary", response_model=CarbonSummaryResponse)
def get_carbon_summary(
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间"),
    device_id: Optional[int] = Query(None, description="设备ID，不传则查询所有"),
    session: Session = Depends(get_session)
):
    """
    获取碳排放汇总报告
    
    按能源类型统计总碳排放量和能源消耗量
    """
    summary = EnergyService.get_carbon_summary(
        session=session,
        start_time=start_time,
        end_time=end_time,
        device_id=device_id
    )
    
    return summary


@router.get("/statistics", response_model=EnergyStatisticsResponse)
def get_energy_statistics(
    energy_type: str = Query(..., description="能源类型"),
    start_time: datetime = Query(..., description="开始时间"),
    end_time: datetime = Query(..., description="结束时间"),
    device_id: Optional[int] = Query(None, description="设备ID，不传则系统级统计"),
    period_type: str = Query("day", description="统计周期: hour/day/month/year"),
    session: Session = Depends(get_session)
):
    """
    计算能源统计数据
    
    统计指定时间段内的总消耗、平均流量、峰值等
    """
    stats = EnergyService.calculate_statistics(
        session=session,
        device_id=device_id,
        energy_type=energy_type,
        start_time=start_time,
        end_time=end_time,
        period_type=period_type
    )
    
    return stats


@router.get("/types", response_model=dict)
def get_energy_types():
    """
    获取支持的能源类型列表
    """
    return {
        "energy_types": [
            {"value": EnergyType.ELECTRICITY, "label": "电力", "unit": "kWh"},
            {"value": EnergyType.WATER, "label": "水", "unit": "m³"},
            {"value": EnergyType.GAS, "label": "燃气", "unit": "m³"},
            {"value": EnergyType.HEAT, "label": "热力", "unit": "GJ"},
            {"value": EnergyType.COOLING, "label": "冷气", "unit": "kWh"},
            {"value": EnergyType.STEAM, "label": "蒸汽", "unit": "t"},
        ],
        "device_categories": [
            {"value": DeviceCategory.LOAD, "label": "用电设备"},
            {"value": DeviceCategory.SOLAR, "label": "光伏发电"},
            {"value": DeviceCategory.WIND, "label": "风力发电"},
            {"value": DeviceCategory.WATER_METER, "label": "水表"},
            {"value": DeviceCategory.GAS_METER, "label": "燃气表"},
            {"value": DeviceCategory.HEAT_METER, "label": "热量表"},
            {"value": DeviceCategory.COOLING_METER, "label": "冷量表"},
            {"value": DeviceCategory.STORAGE, "label": "储能设备"},
            {"value": DeviceCategory.CHARGER, "label": "充电桩"},
        ]
    }


@router.get("/carbon/factors", response_model=dict)
def get_carbon_factors():
    """
    获取各能源类型的碳排放因子
    """
    return {
        "carbon_factors": {
            energy_type: {
                "factor": factor,
                "unit": f"kg CO2/{EnergyService.ENERGY_UNITS.get(energy_type, '')}"
            }
            for energy_type, factor in EnergyService.CARBON_FACTORS.items()
        },
        "description": "碳排放因子参考国家标准，实际使用时可根据地区调整"
    }


@router.post("/carbon/calculate")
def calculate_carbon_manual(
    energy_type: str = Query(..., description="能源类型"),
    consumption: float = Query(..., description="消耗量"),
    session: Session = Depends(get_session)
):
    """
    手动计算碳排放
    
    用于快速计算指定能源消耗的碳排放量
    """
    carbon_factor = EnergyService.CARBON_FACTORS.get(energy_type, 0)
    carbon_emission = consumption * carbon_factor
    unit = EnergyService.ENERGY_UNITS.get(energy_type, "")
    
    return success_response(data={
        "energy_type": energy_type,
        "consumption": consumption,
        "consumption_unit": unit,
        "carbon_factor": carbon_factor,
        "carbon_emission": round(carbon_emission, 2),
        "emission_unit": "kg CO2"
    })
