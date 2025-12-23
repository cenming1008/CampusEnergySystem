from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.tables import DeviceData
from app.services.data_processor import process_device_data

router = APIRouter()

# --- 接口 1: 模拟器上传数据用 (POST) ---
@router.post("/", response_model=DeviceData)
def upload_telemetry(data: DeviceData, session: Session = Depends(get_session)):
    # ✅ 直接调用公共服务，逻辑全都在那边处理
    return process_device_data(
        session=session,
        device_id=data.device_id,
        voltage=data.voltage,
        current=data.current,
        power=data.power,
        energy=data.energy,
        timestamp=data.timestamp
    )

# --- 接口 2: 前端图表获取历史数据用 (GET) ---
# (这部分代码保持不变，不需要修改)
@router.get("/{device_id}", response_model=List[DeviceData])
def read_device_history(device_id: int, limit: int = 50, session: Session = Depends(get_session)):
    statement = (
        select(DeviceData)
        .where(DeviceData.device_id == device_id)
        .order_by(DeviceData.timestamp.desc())
        .limit(limit)
    )
    results = session.exec(statement).all()
    return list(reversed(results))