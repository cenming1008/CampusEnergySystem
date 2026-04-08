"""
设备维护管理API端点
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import MAINTAINER_OR_ADMIN, get_current_user
from app.application.maintenance import (
    cancel_maintenance_use_case,
    complete_maintenance_use_case,
    create_maintenance_record_use_case,
    delete_maintenance_record_use_case,
    get_maintenance_detail_use_case,
    list_device_maintenance_history_use_case,
    list_maintenance_records_use_case,
    list_maintenance_status_options_use_case,
    list_maintenance_type_options_use_case,
    list_overdue_maintenance_use_case,
    list_upcoming_maintenance_use_case,
    start_maintenance_use_case,
    summarize_maintenance_statistics_use_case,
    update_maintenance_record_use_case,
)
from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import DeviceMaintenance, User

router = APIRouter()


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


@router.get("/", response_model=List[DeviceMaintenance])
def get_maintenance_list(
    device_id: Optional[int] = Query(None, description="按设备ID筛选"),
    maintenance_type: Optional[str] = Query(None, description="按维护类型筛选"),
    status: Optional[str] = Query(None, description="按状态筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    limit: int = Query(50, ge=1, le=200, description="返回记录数限制"),
    offset: int = Query(0, ge=0, description="分页偏移量"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
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

    return list_maintenance_records_use_case(
        session=session,
        current_user=current_user,
        device_id=device_id,
        maintenance_type=maintenance_type,
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )


@router.get("/types")
def get_maintenance_types():
    """获取所有支持的维护类型（由 MaintenanceType 枚举生成）"""

    return success_response(data=list_maintenance_type_options_use_case())


@router.get("/statuses")
def get_maintenance_statuses():
    """获取所有维护状态（由 MaintenanceStatus 枚举生成）"""

    return success_response(data=list_maintenance_status_options_use_case())


@router.get("/{maintenance_id}", response_model=DeviceMaintenance)
def get_maintenance_detail(
    maintenance_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取维护记录详情（资源不存在时由全局异常处理器返回 404）"""

    return get_maintenance_detail_use_case(session, current_user, maintenance_id)


@router.post("/", response_model=DeviceMaintenance)
def create_maintenance(
    request: MaintenanceCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """创建维护记录（设备不存在等由全局异常处理器返回 404）"""

    return create_maintenance_record_use_case(
        session=session,
        current_user=current_user,
        device_id=request.device_id,
        maintenance_type=request.maintenance_type,
        scheduled_time=request.scheduled_time,
        title=request.title,
        description=request.description,
        operator=request.operator,
        created_by=request.created_by,
    )


@router.put("/{maintenance_id}", response_model=DeviceMaintenance)
def update_maintenance(
    maintenance_id: int,
    request: MaintenanceUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """更新维护记录（资源不存在等由全局异常处理器处理）"""

    update_data = request.model_dump(exclude_unset=True)
    return update_maintenance_record_use_case(session, current_user, maintenance_id, update_data)


@router.post("/{maintenance_id}/start", response_model=DeviceMaintenance)
def start_maintenance(
    maintenance_id: int,
    request: MaintenanceStartRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """开始维护（将状态改为进行中，资源不存在等由全局异常处理器处理）"""

    return start_maintenance_use_case(session, current_user, maintenance_id, request.operator)


@router.post("/{maintenance_id}/complete", response_model=DeviceMaintenance)
def complete_maintenance(
    maintenance_id: int,
    request: MaintenanceCompleteRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """完成维护（资源不存在等由全局异常处理器处理）"""

    return complete_maintenance_use_case(
        session=session,
        current_user=current_user,
        maintenance_id=maintenance_id,
        result=request.result,
        cost=request.cost,
        parts_replaced=request.parts_replaced,
        next_maintenance_date=request.next_maintenance_date,
    )


@router.post("/{maintenance_id}/cancel", response_model=DeviceMaintenance)
def cancel_maintenance(
    maintenance_id: int,
    request: MaintenanceCancelRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """取消维护（资源不存在等由全局异常处理器处理）"""

    return cancel_maintenance_use_case(session, current_user, maintenance_id, request.reason)


@router.delete("/{maintenance_id}")
def delete_maintenance(
    maintenance_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """删除维护记录（记录不存在时由全局异常处理器返回 404）"""

    result = delete_maintenance_record_use_case(session, current_user, maintenance_id)
    return success_response(message=result.message)


@router.get("/device/{device_id}/history", response_model=List[DeviceMaintenance])
def get_device_maintenance_history(
    device_id: int,
    limit: int = Query(10, ge=1, le=100, description="返回记录数"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    获取设备的维护历史记录

    Args:
        device_id: 设备ID
        limit: 返回记录数

    Returns:
        维护历史列表
    """

    return list_device_maintenance_history_use_case(session, current_user, device_id, limit)


@router.get("/upcoming/list", response_model=List[DeviceMaintenance])
def get_upcoming_maintenance(
    days: int = Query(7, ge=1, le=90, description="未来天数"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    获取即将到来的维护计划

    Args:
        days: 未来天数（1-90天）

    Returns:
        即将进行的维护列表
    """

    return list_upcoming_maintenance_use_case(session, current_user, days)


@router.get("/overdue/list", response_model=List[DeviceMaintenance])
def get_overdue_maintenance(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    获取逾期未完成的维护计划

    Returns:
        逾期维护列表
    """

    return list_overdue_maintenance_use_case(session, current_user)


@router.get("/statistics/summary")
def get_maintenance_statistics(
    device_id: Optional[int] = Query(None, description="设备ID（不指定则统计所有设备）"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
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

    stats = summarize_maintenance_statistics_use_case(
        session,
        current_user,
        device_id,
        start_date,
        end_date,
    )
    return success_response(data=stats)
