"""
设备维护管理API端点
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import DeviceMaintenance, MaintenanceType, MaintenanceStatus
from app.services.maintenance_service import MaintenanceService

router = APIRouter()


# ==================== 请求/响应模型 ====================

class MaintenanceCreateRequest(BaseModel):
    """创建维护记录请求"""
    device_id: int = Field(..., description="设备ID")
    maintenance_type: str = Field(..., description="维护类型")
    scheduled_time: datetime = Field(..., description="计划维护时间")
    title: str = Field(..., description="维护标题")
    description: Optional[str] = Field(None, description="维护描述")
    operator: Optional[str] = Field(None, description="维护人员")
    created_by: Optional[str] = Field(None, description="创建人")


class MaintenanceUpdateRequest(BaseModel):
    """更新维护记录请求"""
    scheduled_time: Optional[datetime] = None
    title: Optional[str] = None
    description: Optional[str] = None
    operator: Optional[str] = None
    cost: Optional[float] = None
    parts_replaced: Optional[str] = None
    result: Optional[str] = None
    next_maintenance_date: Optional[datetime] = None


class MaintenanceStartRequest(BaseModel):
    """开始维护请求"""
    operator: Optional[str] = Field(None, description="维护人员")


class MaintenanceCompleteRequest(BaseModel):
    """完成维护请求"""
    result: Optional[str] = Field(None, description="维护结果/备注")
    cost: Optional[float] = Field(None, description="维护成本")
    parts_replaced: Optional[str] = Field(None, description="更换部件清单（JSON数组字符串）")
    next_maintenance_date: Optional[datetime] = Field(None, description="建议下次维护日期")


class MaintenanceCancelRequest(BaseModel):
    """取消维护请求"""
    reason: Optional[str] = Field(None, description="取消原因")


# ==================== API端点 ====================

@router.get("/", response_model=List[DeviceMaintenance])
def get_maintenance_list(
    device_id: Optional[int] = Query(None, description="按设备ID筛选"),
    maintenance_type: Optional[str] = Query(None, description="按维护类型筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    limit: int = Query(50, ge=1, le=200, description="返回记录数限制"),
    offset: int = Query(0, ge=0, description="分页偏移量"),
    session: Session = Depends(get_session)
):
    """
    获取维护记录列表
    
    支持多条件筛选：
    - device_id: 设备ID
    - maintenance_type: 维护类型（routine/repair/inspection/upgrade/calibration）
    - status: 状态（scheduled/in_progress/completed/cancelled）
    - start_date: 开始日期
    - end_date: 结束日期
    - limit: 返回记录数
    - offset: 分页偏移
    """
    return MaintenanceService.get_maintenance_list(
        session=session,
        device_id=device_id,
        maintenance_type=maintenance_type,
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )


@router.get("/types")
def get_maintenance_types():
    """
    获取所有支持的维护类型
    
    Returns:
        维护类型列表及说明
    """
    types = [
        {
            "value": MaintenanceType.ROUTINE,
            "label": "日常维护",
            "description": "定期的日常保养和检查"
        },
        {
            "value": MaintenanceType.REPAIR,
            "label": "故障维修",
            "description": "设备故障后的修理"
        },
        {
            "value": MaintenanceType.INSPECTION,
            "label": "定期巡检",
            "description": "按计划进行的设备巡检"
        },
        {
            "value": MaintenanceType.UPGRADE,
            "label": "设备升级",
            "description": "设备软硬件升级改造"
        },
        {
            "value": MaintenanceType.CALIBRATION,
            "label": "校准调试",
            "description": "设备精度校准和参数调试"
        }
    ]
    return success_response(data=types)


@router.get("/statuses")
def get_maintenance_statuses():
    """
    获取所有维护状态
    
    Returns:
        维护状态列表及说明
    """
    statuses = [
        {
            "value": MaintenanceStatus.SCHEDULED,
            "label": "已计划",
            "description": "维护已安排，等待执行"
        },
        {
            "value": MaintenanceStatus.IN_PROGRESS,
            "label": "进行中",
            "description": "维护正在进行"
        },
        {
            "value": MaintenanceStatus.COMPLETED,
            "label": "已完成",
            "description": "维护已完成"
        },
        {
            "value": MaintenanceStatus.CANCELLED,
            "label": "已取消",
            "description": "维护已取消"
        }
    ]
    return success_response(data=statuses)


@router.get("/{maintenance_id}", response_model=DeviceMaintenance)
def get_maintenance_detail(
    maintenance_id: int,
    session: Session = Depends(get_session)
):
    """
    获取维护记录详情
    
    Args:
        maintenance_id: 维护记录ID
        
    Returns:
        维护记录详情
    """
    try:
        return MaintenanceService.get_maintenance_by_id(session, maintenance_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=DeviceMaintenance)
def create_maintenance(
    request: MaintenanceCreateRequest,
    session: Session = Depends(get_session)
):
    """
    创建维护记录
    
    Args:
        request: 维护记录创建请求
        
    Returns:
        创建的维护记录
    """
    try:
        return MaintenanceService.create_maintenance(
            session=session,
            device_id=request.device_id,
            maintenance_type=request.maintenance_type,
            scheduled_time=request.scheduled_time,
            title=request.title,
            description=request.description,
            operator=request.operator,
            created_by=request.created_by
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{maintenance_id}", response_model=DeviceMaintenance)
def update_maintenance(
    maintenance_id: int,
    request: MaintenanceUpdateRequest,
    session: Session = Depends(get_session)
):
    """
    更新维护记录
    
    Args:
        maintenance_id: 维护记录ID
        request: 更新请求
        
    Returns:
        更新后的维护记录
    """
    try:
        update_data = request.dict(exclude_unset=True)
        return MaintenanceService.update_maintenance(
            session, maintenance_id, **update_data
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{maintenance_id}/start", response_model=DeviceMaintenance)
def start_maintenance(
    maintenance_id: int,
    request: MaintenanceStartRequest,
    session: Session = Depends(get_session)
):
    """
    开始维护（将状态改为进行中）
    
    Args:
        maintenance_id: 维护记录ID
        request: 开始维护请求
        
    Returns:
        更新后的维护记录
    """
    try:
        return MaintenanceService.start_maintenance(
            session, maintenance_id, request.operator
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{maintenance_id}/complete", response_model=DeviceMaintenance)
def complete_maintenance(
    maintenance_id: int,
    request: MaintenanceCompleteRequest,
    session: Session = Depends(get_session)
):
    """
    完成维护（将状态改为已完成）
    
    Args:
        maintenance_id: 维护记录ID
        request: 完成维护请求
        
    Returns:
        更新后的维护记录
    """
    try:
        return MaintenanceService.complete_maintenance(
            session=session,
            maintenance_id=maintenance_id,
            result=request.result,
            cost=request.cost,
            parts_replaced=request.parts_replaced,
            next_maintenance_date=request.next_maintenance_date
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{maintenance_id}/cancel", response_model=DeviceMaintenance)
def cancel_maintenance(
    maintenance_id: int,
    request: MaintenanceCancelRequest,
    session: Session = Depends(get_session)
):
    """
    取消维护
    
    Args:
        maintenance_id: 维护记录ID
        request: 取消维护请求
        
    Returns:
        更新后的维护记录
    """
    try:
        return MaintenanceService.cancel_maintenance(
            session, maintenance_id, request.reason
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{maintenance_id}")
def delete_maintenance(
    maintenance_id: int,
    session: Session = Depends(get_session)
):
    """
    删除维护记录
    
    Args:
        maintenance_id: 维护记录ID
        
    Returns:
        成功响应
    """
    success = MaintenanceService.delete_maintenance(session, maintenance_id)
    if not success:
        raise HTTPException(status_code=400, detail="删除失败")
    
    return success_response(message=f"维护记录 {maintenance_id} 已删除")


# ==================== 统计和分析端点 ====================

@router.get("/device/{device_id}/history", response_model=List[DeviceMaintenance])
def get_device_maintenance_history(
    device_id: int,
    limit: int = Query(10, ge=1, le=100, description="返回记录数"),
    session: Session = Depends(get_session)
):
    """
    获取设备的维护历史记录
    
    Args:
        device_id: 设备ID
        limit: 返回记录数
        
    Returns:
        维护历史列表
    """
    return MaintenanceService.get_device_maintenance_history(
        session, device_id, limit
    )


@router.get("/upcoming/list", response_model=List[DeviceMaintenance])
def get_upcoming_maintenance(
    days: int = Query(7, ge=1, le=90, description="未来天数"),
    session: Session = Depends(get_session)
):
    """
    获取即将到来的维护计划
    
    Args:
        days: 未来天数（1-90天）
        
    Returns:
        即将进行的维护列表
    """
    return MaintenanceService.get_upcoming_maintenance(session, days)


@router.get("/overdue/list", response_model=List[DeviceMaintenance])
def get_overdue_maintenance(
    session: Session = Depends(get_session)
):
    """
    获取逾期未完成的维护计划
    
    Returns:
        逾期维护列表
    """
    return MaintenanceService.get_overdue_maintenance(session)


@router.get("/statistics/summary")
def get_maintenance_statistics(
    device_id: Optional[int] = Query(None, description="设备ID（不指定则统计所有设备）"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    session: Session = Depends(get_session)
):
    """
    获取维护统计信息
    
    Args:
        device_id: 设备ID（可选）
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        统计信息（总数、按状态/类型统计、成本统计、时长统计等）
    """
    stats = MaintenanceService.get_maintenance_statistics(
        session, device_id, start_date, end_date
    )
    return success_response(data=stats)
