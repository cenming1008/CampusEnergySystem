"""
设备管理API端点
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import Device
from app.services.device_service import DeviceService
from app.services.mqtt_publisher import publish_control_command

router = APIRouter()


@router.get("/", response_model=List[Device])
def get_devices(session: Session = Depends(get_session)):
    """获取所有设备列表"""
    devices = DeviceService.get_all_devices(session)
    return devices


@router.post("/", response_model=Device)
def create_device(
    device: Device,
    session: Session = Depends(get_session)
):
    """创建新设备"""
    return DeviceService.create_device(session, device)


@router.put("/{device_id}", response_model=Device)
def update_device(
    device_id: int,
    device_req: Device,
    session: Session = Depends(get_session)
):
    """更新设备信息"""
    return DeviceService.update_device(
        session,
        device_id,
        name=device_req.name,
        location=device_req.location,
        description=device_req.description
    )


@router.delete("/{device_id}")
def delete_device(
    device_id: int,
    session: Session = Depends(get_session)
):
    """删除设备"""
    device = DeviceService.get_device_by_id(session, device_id)
    DeviceService.delete_device(session, device_id)
    return success_response(message=f"设备 {device.name} 已删除")


@router.post("/{device_id}/toggle")
def toggle_device_status(
    device_id: int,
    active: bool,
    session: Session = Depends(get_session)
):
    """切换设备启停状态"""
    device = DeviceService.toggle_device_status(session, device_id, active)
    
    # 发送MQTT控制指令
    action_code = "start" if active else "stop"
    publish_control_command(device.id, action_code)
    
    return device