"""
巡检运维 API 端点
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import MAINTAINER_OPERATOR_OR_ADMIN, MAINTAINER_OR_ADMIN, get_current_user
from app.core.access_control import (
    ensure_device_access,
    ensure_route_access,
    get_allowed_device_ids,
    get_accessible_plan_ids,
    get_accessible_route_ids,
    get_accessible_task_ids,
)
from app.core.audit import audit_log
from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import (
    InspectionRoute, InspectionPoint, InspectionPlan,
    InspectionTask, InspectionRecord, User
)
from app.services.inspection_service import InspectionService

router = APIRouter()


# ==================== 请求/响应模型 ====================

class RouteCreateRequest(BaseModel):
    """创建巡检路线请求"""
    name: str = Field(..., description="路线名称")
    code: Optional[str] = Field(None, description="路线编码")
    description: Optional[str] = Field(None, description="描述")
    estimated_duration: int = Field(30, description="预计耗时（分钟）")


class RouteUpdateRequest(BaseModel):
    """更新巡检路线请求"""
    name: Optional[str] = Field(None, description="路线名称")
    code: Optional[str] = Field(None, description="路线编码")
    description: Optional[str] = Field(None, description="描述")
    estimated_duration: Optional[int] = Field(None, description="预计耗时（分钟）")
    is_active: Optional[bool] = Field(None, description="是否启用")


class PointCreateRequest(BaseModel):
    """创建巡检点请求"""
    route_id: int = Field(..., description="路线ID")
    name: str = Field(..., description="巡检点名称")
    device_id: Optional[int] = Field(None, description="关联设备ID")
    location: Optional[str] = Field(None, description="位置描述")
    sequence: int = Field(0, description="巡检顺序")
    check_items: Optional[List[str]] = Field(None, description="检查项目")
    qr_code: Optional[str] = Field(None, description="二维码编号")
    is_required: bool = Field(True, description="是否必检")


class PointUpdateRequest(BaseModel):
    """更新巡检点请求（不需要 route_id）"""
    name: Optional[str] = Field(None, description="巡检点名称")
    device_id: Optional[int] = Field(None, description="关联设备ID")
    location: Optional[str] = Field(None, description="位置描述")
    sequence: Optional[int] = Field(None, description="巡检顺序")
    check_items: Optional[List[str]] = Field(None, description="检查项目")
    qr_code: Optional[str] = Field(None, description="二维码编号")
    is_required: Optional[bool] = Field(None, description="是否必检")
    is_active: Optional[bool] = Field(None, description="是否启用")


class PlanCreateRequest(BaseModel):
    """创建巡检计划请求"""
    route_id: int = Field(..., description="巡检路线ID")
    name: str = Field(..., description="计划名称")
    plan_type: str = Field("daily", description="计划类型")
    start_date: datetime = Field(..., description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    execution_time: str = Field("08:00", description="执行时间")
    assigned_to: Optional[str] = Field(None, description="负责人")
    department: Optional[str] = Field(None, description="部门")


class PlanUpdateRequest(BaseModel):
    """更新巡检计划请求"""
    route_id: Optional[int] = Field(None, description="巡检路线ID")
    name: Optional[str] = Field(None, description="计划名称")
    plan_type: Optional[str] = Field(None, description="计划类型")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    execution_time: Optional[str] = Field(None, description="执行时间")
    assigned_to: Optional[str] = Field(None, description="负责人")
    department: Optional[str] = Field(None, description="部门")
    is_active: Optional[bool] = Field(None, description="是否启用")


class TaskCreateRequest(BaseModel):
    """创建巡检任务请求"""
    route_id: int = Field(..., description="路线ID")
    task_date: Optional[datetime] = Field(None, description="任务日期")
    plan_id: Optional[int] = Field(None, description="关联计划ID")
    inspector: Optional[str] = Field(None, description="巡检员")


class RecordSubmitRequest(BaseModel):
    """提交巡检记录请求"""
    task_id: int = Field(..., description="任务ID")
    point_id: int = Field(..., description="巡检点ID")
    result: str = Field("normal", description="检查结果")
    check_details: Optional[dict] = Field(None, description="检查详情")
    meter_reading: Optional[float] = Field(None, description="仪表读数")
    abnormal_description: Optional[str] = Field(None, description="异常描述")
    abnormal_level: Optional[str] = Field(None, description="异常等级")
    images: Optional[List[str]] = Field(None, description="图片列表")
    inspector: Optional[str] = Field(None, description="巡检员")


# ==================== 巡检路线 API ====================

@router.get("/routes", response_model=List[InspectionRoute])
def get_routes(
    is_active: Optional[bool] = Query(None),
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(50, ge=1, le=200, description="每页数量"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取所有巡检路线（支持分页）"""
    routes = InspectionService.get_all_routes(session, is_active, offset, limit)
    accessible_route_ids = get_accessible_route_ids(session, current_user)
    if accessible_route_ids is None:
        return routes
    return [route for route in routes if route.id in accessible_route_ids]


@router.post("/routes", response_model=InspectionRoute)
def create_route(
    req: RouteCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """创建巡检路线（业务异常由全局异常处理器处理）"""
    result = InspectionService.create_route(
        session=session,
        name=req.name,
        code=req.code,
        description=req.description,
        estimated_duration=req.estimated_duration
    )
    audit_log("inspection.route.create", current_user.username, f"route:{result.id}", role=current_user.role)
    return result


@router.get("/routes/{route_id}", response_model=InspectionRoute)
def get_route(
    route_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取巡检路线详情"""
    ensure_route_access(session, current_user, route_id)
    return InspectionService.get_route_by_id(session, route_id)


@router.get("/routes/{route_id}/points", response_model=List[InspectionPoint])
def get_route_points(
    route_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取路线的所有巡检点"""
    ensure_route_access(session, current_user, route_id)
    points = InspectionService.get_route_points(session, route_id)
    allowed_device_ids = get_allowed_device_ids(session, current_user)
    if allowed_device_ids is None:
        return points
    return [
        point for point in points
        if point.device_id is None or point.device_id in allowed_device_ids
    ]


@router.put("/routes/{route_id}", response_model=InspectionRoute)
def update_route(
    route_id: int,
    req: RouteUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """更新巡检路线"""
    ensure_route_access(session, current_user, route_id)
    update_fields = {k: v for k, v in req.model_dump().items() if v is not None}
    result = InspectionService.update_route(session, route_id, **update_fields)
    audit_log("inspection.route.update", current_user.username, f"route:{route_id}", role=current_user.role)
    return result


@router.delete("/routes/{route_id}")
def delete_route(
    route_id: int,
    force: bool = Query(False, description="是否强制删除（同时删除关联的巡检点、计划、任务）"),
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """删除巡检路线（冲突时由全局异常处理器返回 409）"""
    ensure_route_access(session, current_user, route_id)
    InspectionService.delete_route(session, route_id, force=force)
    audit_log("inspection.route.delete", current_user.username, f"route:{route_id}", force=force, role=current_user.role)
    return success_response(message="删除成功")


# ==================== 巡检点 API ====================

@router.post("/points", response_model=InspectionPoint)
def create_point(
    req: PointCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """添加巡检点（路线/设备不存在等由全局异常处理器处理）"""
    ensure_route_access(session, current_user, req.route_id)
    if req.device_id is not None:
        ensure_device_access(session, current_user, req.device_id)
    result = InspectionService.add_point_to_route(
        session=session,
        route_id=req.route_id,
        name=req.name,
        device_id=req.device_id,
        location=req.location,
        sequence=req.sequence,
        check_items=req.check_items,
        qr_code=req.qr_code,
        is_required=req.is_required
    )
    audit_log("inspection.point.create", current_user.username, f"route:{req.route_id}", role=current_user.role)
    return result


@router.put("/points/{point_id}", response_model=InspectionPoint)
def update_point(
    point_id: int,
    req: PointUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """更新巡检点"""
    point = session.get(InspectionPoint, point_id)
    if point is not None:
        ensure_route_access(session, current_user, point.route_id)
    if req.device_id is not None:
        ensure_device_access(session, current_user, req.device_id)
    # 只传递非 None 的字段
    update_fields = {k: v for k, v in req.model_dump().items() if v is not None}
    result = InspectionService.update_point(session, point_id, **update_fields)
    audit_log("inspection.point.update", current_user.username, f"point:{point_id}", role=current_user.role)
    return result


@router.delete("/points/{point_id}")
def delete_point(
    point_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """删除巡检点"""
    point = session.get(InspectionPoint, point_id)
    if point is not None:
        ensure_route_access(session, current_user, point.route_id)
    InspectionService.delete_point(session, point_id)
    audit_log("inspection.point.delete", current_user.username, f"point:{point_id}", role=current_user.role)
    return success_response(message="删除成功")


# ==================== 巡检计划 API ====================

@router.get("/plans", response_model=List[InspectionPlan])
def get_plans(
    is_active: Optional[bool] = Query(None),
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(50, ge=1, le=200, description="每页数量"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取所有巡检计划（支持分页）"""
    plans = InspectionService.get_all_plans(session, is_active, offset, limit)
    accessible_plan_ids = get_accessible_plan_ids(session, current_user)
    if accessible_plan_ids is None:
        return plans
    return [plan for plan in plans if plan.id in accessible_plan_ids]


@router.post("/plans", response_model=InspectionPlan)
def create_plan(
    req: PlanCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """创建巡检计划（路线不存在等由全局异常处理器处理）"""
    ensure_route_access(session, current_user, req.route_id)
    result = InspectionService.create_plan(
        session=session,
        route_id=req.route_id,
        name=req.name,
        plan_type=req.plan_type,
        start_date=req.start_date,
        end_date=req.end_date,
        execution_time=req.execution_time,
        assigned_to=req.assigned_to,
        department=req.department
    )
    audit_log("inspection.plan.create", current_user.username, f"route:{req.route_id}", role=current_user.role)
    return result


@router.get("/plans/{plan_id}", response_model=InspectionPlan)
def get_plan(
    plan_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取巡检计划详情"""
    accessible_plan_ids = get_accessible_plan_ids(session, current_user)
    if accessible_plan_ids is not None and plan_id not in accessible_plan_ids:
        ensure_route_access(session, current_user, InspectionService.get_plan_by_id(session, plan_id).route_id)
    return InspectionService.get_plan_by_id(session, plan_id)


@router.put("/plans/{plan_id}", response_model=InspectionPlan)
def update_plan(
    plan_id: int,
    req: PlanUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """更新巡检计划"""
    plan = InspectionService.get_plan_by_id(session, plan_id)
    ensure_route_access(session, current_user, plan.route_id)
    if req.route_id is not None:
        ensure_route_access(session, current_user, req.route_id)
    update_fields = {k: v for k, v in req.model_dump().items() if v is not None}
    result = InspectionService.update_plan(session, plan_id, **update_fields)
    audit_log("inspection.plan.update", current_user.username, f"plan:{plan_id}", role=current_user.role)
    return result


@router.delete("/plans/{plan_id}")
def delete_plan(
    plan_id: int,
    force: bool = Query(False, description="是否强制删除（取消关联任务的计划关联）"),
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """删除巡检计划（冲突时由全局异常处理器返回 409）"""
    plan = InspectionService.get_plan_by_id(session, plan_id)
    ensure_route_access(session, current_user, plan.route_id)
    InspectionService.delete_plan(session, plan_id, force=force)
    audit_log("inspection.plan.delete", current_user.username, f"plan:{plan_id}", force=force, role=current_user.role)
    return success_response(message="删除成功")


# ==================== 巡检任务 API ====================

@router.get("/tasks", response_model=List[InspectionTask])
def get_tasks(
    status: Optional[str] = Query(None),
    inspector: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取巡检任务列表"""
    return InspectionService.get_tasks(
        session=session,
        status=status,
        inspector=inspector,
        start_date=start_date,
        end_date=end_date,
        allowed_route_ids=get_accessible_route_ids(session, current_user),
        limit=limit
    )


@router.get("/tasks/today", response_model=List[InspectionTask])
def get_today_tasks(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取今日巡检任务"""
    return InspectionService.get_today_tasks(
        session,
        allowed_route_ids=get_accessible_route_ids(session, current_user),
    )


@router.get("/tasks/pending", response_model=List[InspectionTask])
def get_pending_tasks(
    limit: int = Query(10),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取待执行的巡检任务"""
    return InspectionService.get_pending_tasks(
        session,
        limit,
        allowed_route_ids=get_accessible_route_ids(session, current_user),
    )


@router.post("/tasks", response_model=InspectionTask)
def create_task(
    req: TaskCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """创建巡检任务（路线/计划不存在等由全局异常处理器处理）"""
    ensure_route_access(session, current_user, req.route_id)
    result = InspectionService.create_task(
        session=session,
        route_id=req.route_id,
        task_date=req.task_date,
        plan_id=req.plan_id,
        inspector=req.inspector
    )
    audit_log("inspection.task.create", current_user.username, f"route:{req.route_id}", role=current_user.role)
    return result


@router.get("/tasks/{task_id}", response_model=InspectionTask)
def get_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取巡检任务详情"""
    accessible_task_ids = get_accessible_task_ids(session, current_user)
    if accessible_task_ids is not None and task_id not in accessible_task_ids:
        ensure_route_access(session, current_user, InspectionService.get_task_by_id(session, task_id).route_id)
    return InspectionService.get_task_by_id(session, task_id)


@router.post("/tasks/{task_id}/start", response_model=InspectionTask)
def start_task(
    task_id: int,
    inspector: Optional[str] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OPERATOR_OR_ADMIN),
):
    """开始执行巡检任务（状态冲突时由全局异常处理器返回 409）"""
    task = InspectionService.get_task_by_id(session, task_id)
    ensure_route_access(session, current_user, task.route_id)
    result = InspectionService.start_task(session, task_id, inspector or current_user.username)
    audit_log("inspection.task.start", current_user.username, f"task:{task_id}", role=current_user.role)
    return result


@router.post("/tasks/{task_id}/complete", response_model=InspectionTask)
def complete_task(
    task_id: int,
    remark: Optional[str] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OPERATOR_OR_ADMIN),
):
    """完成巡检任务（状态冲突时由全局异常处理器返回 409）"""
    task = InspectionService.get_task_by_id(session, task_id)
    ensure_route_access(session, current_user, task.route_id)
    result = InspectionService.complete_task(session, task_id, remark)
    audit_log("inspection.task.complete", current_user.username, f"task:{task_id}", remark=remark, role=current_user.role)
    return result


@router.get("/tasks/{task_id}/records", response_model=List[InspectionRecord])
def get_task_records(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取任务的巡检记录"""
    task = InspectionService.get_task_by_id(session, task_id)
    ensure_route_access(session, current_user, task.route_id)
    return InspectionService.get_task_records(session, task_id)


# ==================== 巡检记录 API ====================

@router.post("/records", response_model=InspectionRecord)
def submit_record(
    req: RecordSubmitRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OPERATOR_OR_ADMIN),
):
    """提交巡检记录（冲突/状态错误由全局异常处理器返回 409）"""
    task = InspectionService.get_task_by_id(session, req.task_id)
    ensure_route_access(session, current_user, task.route_id)
    point = session.get(InspectionPoint, req.point_id)
    if point is not None and point.device_id is not None:
        ensure_device_access(session, current_user, point.device_id)
    result = InspectionService.submit_inspection_record(
        session=session,
        task_id=req.task_id,
        point_id=req.point_id,
        result=req.result,
        check_details=req.check_details,
        meter_reading=req.meter_reading,
        abnormal_description=req.abnormal_description,
        abnormal_level=req.abnormal_level,
        images=req.images,
        inspector=req.inspector or current_user.username
    )
    audit_log("inspection.record.submit", current_user.username, f"task:{req.task_id}", point_id=req.point_id, role=current_user.role)
    return result


# ==================== 统计 API ====================

@router.get("/statistics")
def get_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取巡检统计信息"""
    stats = InspectionService.get_inspection_statistics(
        session=session,
        start_date=start_date,
        end_date=end_date,
        allowed_route_ids=get_accessible_route_ids(session, current_user),
    )
    return success_response(data=stats)
