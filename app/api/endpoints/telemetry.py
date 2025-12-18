from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.database import get_session
from app.core.config import load_thresholds
from app.models.tables import DeviceData, Alarm

router = APIRouter()

# --- 接口 1: 模拟器上传数据用 (POST) ---
@router.post("/", response_model=DeviceData)
def upload_telemetry(data: DeviceData, session: Session = Depends(get_session)):
    # 1. 保存数据
    session.add(data)
    
    # 2. 简单的阈值判断逻辑 (从配置加载)
    settings = load_thresholds()
    defaults = settings.get("default", {})
    # 获取设备特定阈值，如果没有则用默认值
    dev_cfg = settings.get("device_thresholds", {}).get(str(data.device_id), {})
    
    limit_current = dev_cfg.get("current_max", defaults.get("current_max", 45.0))
    limit_v_max = defaults.get("voltage_max", 250.0)
    limit_v_min = defaults.get("voltage_min", 190.0)

    # 3. 产生报警
    if data.current > limit_current:
        msg = f"⚠️ 过载报警! 当前: {data.current}A (上限: {limit_current}A)"
        session.add(Alarm(device_id=data.device_id, message=msg, timestamp=data.timestamp))
        print(f"!!! 报警 [ID:{data.device_id}] {msg}")

    if data.voltage > limit_v_max or data.voltage < limit_v_min:
        msg = f"⚡ 电压异常! 读数: {data.voltage}V"
        session.add(Alarm(device_id=data.device_id, message=msg, timestamp=data.timestamp))
        print(f"!!! 报警 [ID:{data.device_id}] {msg}")

    session.commit()
    session.refresh(data)
    return data

# --- 接口 2: 前端图表获取历史数据用 (GET) ---
@router.get("/{device_id}", response_model=List[DeviceData])
def read_device_history(device_id: int, limit: int = 50, session: Session = Depends(get_session)):
    """
    获取指定设备的最近 N 条数据，用于绘制 Echarts 折线图
    """
    statement = (
        select(DeviceData)
        .where(DeviceData.device_id == device_id)
        .order_by(DeviceData.timestamp.desc()) # 先按时间倒序取最新的50条
        .limit(limit)
    )
    results = session.exec(statement).all()
    
    # ⚠️ 关键点：Echarts需要时间从左到右(旧->新)，但数据库查出来是(新->旧)
    # 所以这里必须反转列表
    return list(reversed(results))