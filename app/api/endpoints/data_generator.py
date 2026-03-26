"""
数据生成API端点
用于生成模拟数据用于训练和测试
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlmodel import Session

from app.api.deps import ADMIN_ONLY
from app.api.endpoint_utils import bad_request_from_value_error, log_endpoint_exception
from app.core.audit import audit_log
from app.core.database import get_session
from app.core.response import success_response
from app.integrations.forecasting import ForecastAdapter
from app.models.tables import User

router = APIRouter()
VALID_DATA_TYPES = {"load", "solar", "wind"}


def _get_forecast_adapter() -> ForecastAdapter:
    """创建预测适配器实例。"""
    return ForecastAdapter()


def _validate_data_type(data_type: str) -> str:
    normalized_type = data_type.lower()
    if normalized_type not in VALID_DATA_TYPES:
        raise HTTPException(
            status_code=400,
            detail="data_type 必须是 'load', 'solar' 或 'wind'"
        )
    return normalized_type


@router.post("/generate/device/{device_id}")
def generate_device_data(
    device_id: int,
    days: int = Body(60, ge=1, le=365, description="生成数据的天数"),
    interval_minutes: int = Body(60, ge=1, le=1440, description="数据间隔（分钟）"),
    data_type: str = Body("load", description="数据类型：load/solar/wind"),
    clear_existing: bool = Body(False, description="是否清除现有数据"),
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    """
    为指定设备生成模拟数据
    
    用于LSTM模型训练和测试
    """
    data_type = _validate_data_type(data_type)
    
    try:
        count = _get_forecast_adapter().generate_device_data(
            session=session,
            device_id=device_id,
            days=days,
            interval_minutes=interval_minutes,
            data_type=data_type,
            clear_existing=clear_existing
        )
        
        audit_log(
            "data_generator.generate_device",
            current_user.username,
            f"device:{device_id}",
            count=count,
            data_type=data_type,
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
    except HTTPException:
        raise
    except ValueError as exc:
        raise bad_request_from_value_error(exc) from exc
    except Exception as exc:
        log_endpoint_exception(
            f"生成设备模拟数据失败 device_id={device_id}, days={days}, interval_minutes={interval_minutes}, data_type={data_type}",
            exc,
        )
        raise HTTPException(status_code=500, detail="生成数据失败")


@router.post("/generate/all")
def generate_all_devices_data(
    days: int = Body(60, ge=1, le=365, description="生成数据的天数"),
    interval_minutes: int = Body(60, ge=1, le=1440, description="数据间隔（分钟）"),
    clear_existing: bool = Body(False, description="是否清除现有数据"),
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    """
    为所有活动设备生成模拟数据
    
    根据设备类型自动选择数据类型：
    - 包含"solar"或"光伏"的设备 → 光伏数据
    - 包含"wind"或"风电"的设备 → 风电数据
    - 其他设备 → 负荷数据
    """
    try:
        total_count = _get_forecast_adapter().generate_system_data(
            session=session,
            days=days,
            interval_minutes=interval_minutes,
            clear_existing=clear_existing
        )
        
        audit_log(
            "data_generator.generate_all",
            current_user.username,
            "device:*",
            total_count=total_count,
        )
        return success_response(
            data={
                "days": days,
                "interval_minutes": interval_minutes,
                "total_count": total_count
            },
            message=f"成功为所有设备生成 {total_count} 条数据"
        )
    except Exception as exc:
        log_endpoint_exception(
            f"生成全量模拟数据失败 days={days}, interval_minutes={interval_minutes}, clear_existing={clear_existing}",
            exc,
        )
        raise HTTPException(status_code=500, detail="生成数据失败")


@router.delete("/clear/{device_id}")
def clear_device_data(
    device_id: int,
    days: Optional[int] = Query(None, description="清除最近N天的数据，不提供则清除所有"),
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    """
    清除指定设备的数据
    """
    try:
        _get_forecast_adapter().clear_device_data(session, device_id=device_id, days=days)
        audit_log("data_generator.clear_device", current_user.username, f"device:{device_id}", days=days)
        
        return success_response(
            data={"device_id": device_id, "days": days},
            message="数据清除完成"
        )
    except ValueError as exc:
        raise bad_request_from_value_error(exc) from exc
    except Exception as exc:
        log_endpoint_exception(f"清除模拟数据失败 device_id={device_id}, days={days}", exc)
        raise HTTPException(status_code=500, detail="清除数据失败")


@router.get("/stats/{device_id}")
def get_device_data_stats(
    device_id: int,
    session: Session = Depends(get_session)
):
    """
    获取设备数据统计信息
    """
    from sqlmodel import select, func
    from app.models.tables import EnergyData
    
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
