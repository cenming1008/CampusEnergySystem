"""
故障诊断API端点
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.services.fdd_service import FDDService

router = APIRouter()


@router.get("/stats")
def get_fault_diagnosis_stats(session: Session = Depends(get_session)):
    """获取设备故障诊断统计"""
    return FDDService.get_fault_diagnosis_stats(session)