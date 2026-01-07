"""
数据分析API端点
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.services.analysis_service import AnalysisService

router = APIRouter()


@router.get("/{device_id}")
def analyze_device(
    device_id: int,
    session: Session = Depends(get_session)
):
    """获取设备数据分析"""
    return AnalysisService.analyze_device(session, device_id)