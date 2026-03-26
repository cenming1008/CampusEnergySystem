"""
数据分析API端点
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.deps import get_current_user
from app.application.analysis import analyze_device_use_case
from app.core.access_control import ensure_device_access
from app.core.database import get_session
from app.models.tables import User

router = APIRouter()


@router.get("/{device_id}")
def analyze_device(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取设备数据分析"""
    ensure_device_access(session, current_user, device_id)
    return analyze_device_use_case(session, device_id)
