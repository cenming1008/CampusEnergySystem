"""
数据生成API端点
用于生成模拟数据用于训练和测试
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlmodel import Session

from app.core.database import get_session
from app.core.response import success_response
from app.services.forecast_adapter import ForecastAdapter

router = APIRouter()


@router.post("/generate/device/{device_id}")
def generate_device_data(
    device_id: int,
    days: int = Body(60, ge=1, le=365, description="生成数据的天数"),
    interval_minutes: int = Body(60, ge=1, le=1440, description="数据间隔（分钟）"),
    data_type: str = Body("load", description="数据类型：load/solar/wind"),
    clear_existing: bool = Body(False, description="是否清除现有数据"),
    session: Session = Depends(get_session)
):
    """
    为指定设备生成模拟数据
    
    用于LSTM模型训练和测试
    """
    if data_type not in ["load", "solar", "wind"]:
        raise HTTPException(
            status_code=400,
            detail="data_type 必须是 'load', 'solar' 或 'wind'"
        )
    
    try:
        adapter = ForecastAdapter()
        
        # 生成数据（clear_existing 在方法内部处理）
        count = adapter.generate_device_data(
            session=session,
            device_id=device_id,
            days=days,
            interval_minutes=interval_minutes,
            data_type=data_type,
            clear_existing=clear_existing
        )
        
        return success_response(
            data={
                "device_id": device_id,
                "data_type": data_type,
                "days": days,
                "interval_minutes": interval_minutes,
                "count": count
            },
            message=f"成功生成 {count} 条数据"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成数据失败: {str(e)}"
        )


@router.post("/generate/all")
def generate_all_devices_data(
    days: int = Body(60, ge=1, le=365, description="生成数据的天数"),
    interval_minutes: int = Body(60, ge=1, le=1440, description="数据间隔（分钟）"),
    clear_existing: bool = Body(False, description="是否清除现有数据"),
    session: Session = Depends(get_session)
):
    """
    为所有活动设备生成模拟数据
    
    根据设备类型自动选择数据类型：
    - 包含"solar"或"光伏"的设备 → 光伏数据
    - 包含"wind"或"风电"的设备 → 风电数据
    - 其他设备 → 负荷数据
    """
    try:
        adapter = ForecastAdapter()
        
        # 生成数据（clear_existing 在方法内部处理）
        total_count = adapter.generate_system_data(
            session=session,
            days=days,
            interval_minutes=interval_minutes,
            clear_existing=clear_existing
        )
        
        return success_response(
            data={
                "days": days,
                "interval_minutes": interval_minutes,
                "total_count": total_count
            },
            message=f"成功为所有设备生成 {total_count} 条数据"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成数据失败: {str(e)}"
        )


@router.delete("/clear/{device_id}")
def clear_device_data(
    device_id: int,
    days: Optional[int] = Query(None, description="清除最近N天的数据，不提供则清除所有"),
    session: Session = Depends(get_session)
):
    """
    清除指定设备的数据
    """
    try:
        adapter = ForecastAdapter()
        adapter.clear_device_data(session, device_id=device_id, days=days)
        
        return success_response(
            data={"device_id": device_id, "days": days},
            message="数据清除完成"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"清除数据失败: {str(e)}"
        )


@router.get("/stats/{device_id}")
def get_device_data_stats(
    device_id: int,
    session: Session = Depends(get_session)
):
    """
    获取设备数据统计信息
    """
    from sqlmodel import select, func
    from app.models.tables import EnergyData, EnergyType
    
    # 统计总数据量
    total_count = session.exec(
        select(func.count(EnergyData.device_id))
        .where(EnergyData.device_id == device_id)
    ).one()
    
    # 获取最早和最晚数据时间
    earliest = session.exec(
        select(EnergyData.timestamp)
        .where(EnergyData.device_id == device_id)
        .order_by(EnergyData.timestamp.asc())
        .limit(1)
    ).first()
    
    latest = session.exec(
        select(EnergyData.timestamp)
        .where(EnergyData.device_id == device_id)
        .order_by(EnergyData.timestamp.desc())
        .limit(1)
    ).first()
    
    # 计算数据天数
    days = 0
    if earliest and latest:
        days = (latest - earliest).days + 1
    
    return success_response(
        data={
            "device_id": device_id,
            "total_count": total_count,
            "earliest_time": earliest.isoformat() if earliest else None,
            "latest_time": latest.isoformat() if latest else None,
            "days": days
        }
    )
