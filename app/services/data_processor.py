"""
设备数据处理

- 写入设备遥测数据
- 基于阈值生成报警
"""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Session

from app.core.config import load_thresholds
from app.core.logger import logger
from app.models.tables import Alarm, DeviceData


def process_device_data(
    session: Session,
    device_id: int,
    voltage: float,
    current: float,
    power: float,
    energy: float,
    timestamp: datetime,
) -> DeviceData:
    """写入一条设备数据并按阈值生成报警（如触发）。"""
    new_record = DeviceData(
        device_id=device_id,
        voltage=voltage,
        current=current,
        power=power,
        energy=energy,
        timestamp=timestamp,
    )
    session.add(new_record)

    cfg = load_thresholds()
    defaults = cfg.get("default", {})
    dev_cfg = cfg.get("device_thresholds", {}).get(str(device_id), {})

    limit_current = dev_cfg.get("current_max", defaults.get("current_max", 45.0))
    limit_v_max = defaults.get("voltage_max", 250.0)
    limit_v_min = defaults.get("voltage_min", 190.0)

    if current > limit_current:
        msg = f"⚠️ 过载报警! 当前: {current}A (上限: {limit_current}A)"
        logger.warning(f"Alarm triggered: device_id={device_id} type=overload msg={msg}")
        session.add(Alarm(device_id=device_id, message=msg, timestamp=timestamp, is_resolved=False))

    if voltage > limit_v_max or voltage < limit_v_min:
        msg = f"⚡ 电压异常! 读数: {voltage}V"
        logger.warning(f"Alarm triggered: device_id={device_id} type=voltage msg={msg}")
        session.add(Alarm(device_id=device_id, message=msg, timestamp=timestamp, is_resolved=False))

    session.commit()
    session.refresh(new_record)
    return new_record