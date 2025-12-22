from datetime import datetime
from sqlmodel import Session
from app.models.tables import DeviceData, Alarm
from app.core.config import load_thresholds

def process_device_data(session: Session, device_id: int, voltage: float, current: float, power: float, energy: float, timestamp: datetime) -> DeviceData:
    """
    统一处理设备数据：
    1. 保存遥测数据到数据库
    2. 加载阈值配置
    3. 判断是否报警并生成报警记录
    """
    
    # 1. 准备数据记录
    new_record = DeviceData(
        device_id=device_id,
        voltage=voltage,
        current=current,
        power=power,
        energy=energy,
        timestamp=timestamp
    )
    session.add(new_record)

    # 2. 加载配置 (统一逻辑)
    settings = load_thresholds()
    defaults = settings.get("default", {})
    # 获取特定设备的阈值，如果没有则回退到默认值
    dev_cfg = settings.get("device_thresholds", {}).get(str(device_id), {})

    limit_current = dev_cfg.get("current_max", defaults.get("current_max", 45.0))
    limit_v_max = defaults.get("voltage_max", 250.0)
    limit_v_min = defaults.get("voltage_min", 190.0)

    # 3. 报警判断逻辑
    
    # [电流过载报警]
    if current > limit_current:
        msg = f"⚠️ 过载报警! 当前: {current}A (上限: {limit_current}A)"
        # 打印日志方便调试
        print(f"🚨 [报警 ID:{device_id}] {msg}")
        session.add(Alarm(device_id=device_id, message=msg, timestamp=timestamp, is_resolved=False))

    # [电压异常报警] - 之前 MQTT Worker 里漏掉了这个，现在统一补上
    if voltage > limit_v_max or voltage < limit_v_min:
        msg = f"⚡ 电压异常! 读数: {voltage}V"
        print(f"🚨 [报警 ID:{device_id}] {msg}")
        session.add(Alarm(device_id=device_id, message=msg, timestamp=timestamp, is_resolved=False))

    # 4. 提交事务
    session.commit()
    session.refresh(new_record)
    
    return new_record