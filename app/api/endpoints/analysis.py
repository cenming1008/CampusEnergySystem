from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from datetime import datetime, time
from app.core.database import get_session
from app.core.config import load_thresholds
from app.models.tables import DeviceData, Device 

router = APIRouter()

@router.get("/{device_id}")
def analyze_device(device_id: int, session: Session = Depends(get_session)):
    # 1. 先查设备状态
    device = session.get(Device, device_id)
    is_active = device.is_active if device else False # 获取开关状态

    # 加载配置
    settings = load_thresholds()
    price_per_kwh = settings.get("default", {}).get("electricity_price", 0.85)

    now = datetime.now()
    today_start = datetime.combine(now.date(), time.min)
    
    # 2. 获取数据库里【最后一条】数据
    # 哪怕它是 1 小时前的数据，也照样拿出来，不要改它
    latest = session.exec(
        select(DeviceData)
        .where(DeviceData.device_id == device_id)
        .order_by(DeviceData.timestamp.desc())
        .limit(1)
    ).first()
    
    if not latest:
        return {
            "device_id": device_id,
            "is_active": is_active, # 把状态告诉前端
            "current_power": 0, "today_energy": 0, "today_cost": 0,
            "voltage": 0, "current": 0
        }

    # 3. 计算今日能耗
    first_today = session.exec(
        select(DeviceData)
        .where(DeviceData.device_id == device_id)
        .where(DeviceData.timestamp >= today_start)
        .order_by(DeviceData.timestamp.asc())
        .limit(1)
    ).first()
    
    today_kwh = (latest.energy - first_today.energy) if first_today else 0
    today_cost = today_kwh * price_per_kwh

    return {
        "device_id": device_id,
        "is_active": is_active,     # 👈 关键：告诉前端设备是开是关
        "current_power": round(latest.power, 2), # 👈 关键：直接返回最后的值，不归零
        "voltage": round(latest.voltage, 1),
        "current": round(latest.current, 2),
        "today_energy": round(today_kwh, 2),
        "today_cost": round(today_cost, 2),
    }