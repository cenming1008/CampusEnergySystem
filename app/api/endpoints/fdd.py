"""
故障诊断API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.services.fdd_service import FDDService

router = APIRouter()


@router.get("/stats")
def get_fault_diagnosis_stats(session: Session = Depends(get_session)):
    """
    获取所有设备的故障诊断统计
    
    返回所有设备的健康分数、报警数量和状态信息
    """
    return FDDService.get_fault_diagnosis_stats(session)


@router.get("/diagnose/{device_id}")
def diagnose_device(device_id: int, session: Session = Depends(get_session)):
    """
    诊断指定设备的健康状况
    
    Args:
        device_id: 设备ID
        
    Returns:
        设备诊断结果，包括：
        - device_id: 设备ID
        - device_name: 设备名称
        - health_score: 健康分数（0-100）
        - suggestions: 诊断建议列表
        
    Raises:
        HTTPException: 设备不存在时返回404
    """
    result = FDDService.diagnose_device(session, device_id)
    
    # 如果设备不存在，返回404错误
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result