"""
遥测数据API端点
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.tables import DeviceData
from app.services.data_processor import process_device_data

router = APIRouter()


@router.post("/", response_model=DeviceData)
def upload_telemetry(
    data: DeviceData,
    session: Session = Depends(get_session)
):
    """接收设备上传的遥测数据"""
    return process_device_data(
        session=session,
        device_id=data.device_id,
        voltage=data.voltage,
        current=data.current,
        power=data.power,
        energy=data.energy,
        timestamp=data.timestamp
    )


@router.get("/{device_id}", response_model=List[DeviceData])
def get_device_history(
    device_id: int,
    limit: int = 50,
    session: Session = Depends(get_session)
):
    """获取设备历史数据"""
    statement = (
        select(DeviceData)
        .where(DeviceData.device_id == device_id)
        .order_by(DeviceData.timestamp.desc())
        .limit(limit)
    )
    results = session.exec(statement).all()
    return list(reversed(results))