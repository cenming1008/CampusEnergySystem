"""
数据分析API端点
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.application.analysis import analyze_device_use_case
from app.core.database import get_session

router = APIRouter()


@router.get("/{device_id}")
def analyze_device(
    device_id: int,
    session: Session = Depends(get_session)
):
    """获取设备数据分析"""
    return analyze_device_use_case(session, device_id)
