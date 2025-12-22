from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.tables import Device
from app.services.mqtt_publisher import publish_control_command

router = APIRouter()

# ---原有代码保持不变---
@router.post("/", response_model=Device)
def create_device(device: Device, session: Session = Depends(get_session)):
    session.add(device)
    try:
        session.commit()
        session.refresh(device)
        return device
    except Exception:
        session.rollback()
        existing = session.exec(select(Device).where(Device.sn == device.sn)).first()
        if existing: return existing
        raise HTTPException(status_code=400, detail="添加失败")

@router.get("/", response_model=List[Device])
def read_devices(session: Session = Depends(get_session)):
    return session.exec(select(Device).order_by(Device.id)).all()

# --- 👇 新增代码：删除设备 ---
@router.delete("/{device_id}")
def delete_device(device_id: int, session: Session = Depends(get_session)):
    device = session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    session.delete(device)
    session.commit()
    return {"ok": True, "message": f"设备 {device.name} 已删除"}

# --- 👇 新增代码：修改设备信息 ---
@router.put("/{device_id}", response_model=Device)
def update_device(device_id: int, device_req: Device, session: Session = Depends(get_session)):
    # 1. 查
    db_device = session.get(Device, device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    # 2. 改 (排除 id, sn 等关键字段，只允许改名称、位置、描述)
    db_device.name = device_req.name
    db_device.location = device_req.location
    db_device.description = device_req.description
    
    # 3. 存
    session.add(db_device)
    session.commit()
    session.refresh(db_device)
    return db_device

# ---设备切换启停---
@router.post("/{device_id}/toggle")
def toggle_device_status(device_id: int, active: bool, session: Session = Depends(get_session)):
    device = session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    # 1. 更新数据库状态
    device.is_active = active
    session.add(device)
    session.commit()
    session.refresh(device)

    status_text = "启动" if active else "停止"
    action_code = "start" if active else "stop"

    # 👇 2. 发送 MQTT 指令 (反向控制核心)
    publish_control_command(device.id, action_code)

    print(f"✅ 设备{device.name} (ID:{device_id}) 状态已更新为: {status_text}")
    return device