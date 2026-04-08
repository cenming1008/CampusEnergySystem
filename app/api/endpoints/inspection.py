"""
巡检运维 API 端点
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import MAINTAINER_OPERATOR_OR_ADMIN, MAINTAINER_OR_ADMIN, get_current_user
from app.application.inspection import (
    complete_inspection_task_use_case,
    create_inspection_plan_use_case,
    create_inspection_point_use_case,
    create_inspection_route_use_case,
    create_inspection_task_use_case,
    delete_inspection_plan_use_case,
    delete_inspection_point_use_case,
    delete_inspection_route_use_case,
    get_accessible_plan_use_case,
    get_accessible_route_use_case,
    get_accessible_task_use_case,
    get_inspection_statistics_use_case,
    list_accessible_plans_use_case,
    list_accessible_routes_use_case,
    list_accessible_tasks_use_case,
    list_pending_inspection_tasks_use_case,
    list_route_points_use_case,
    list_task_records_use_case,
    list_today_inspection_tasks_use_case,
    start_inspection_task_use_case,
    submit_inspection_record_use_case,
    update_inspection_plan_use_case,
    update_inspection_point_use_case,
    update_inspection_route_use_case,
)
from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import (
    InspectionPlan,
    InspectionPoint,
    InspectionRecord,
    InspectionRoute,
    InspectionTask,
    User,
)

router = APIRouter()


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


@router.get("/routes", response_model=List[InspectionRoute])
def get_routes(
    is_active: Optional[bool] = Query(None),
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(50, ge=1, le=200, description="每页数量"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取所有巡检路线（支持分页）"""

    return list_accessible_routes_use_case(session, current_user, is_active, offset, limit)


@router.post("/routes", response_model=InspectionRoute)
def create_route(
    req: RouteCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """创建巡检路线（业务异常由全局异常处理器处理）"""

    return create_inspection_route_use_case(
        session=session,
        current_user=current_user,
        name=req.name,
        code=req.code,
        description=req.description,
        estimated_duration=req.estimated_duration,
    )


@router.get("/routes/{route_id}", response_model=InspectionRoute)
def get_route(
    route_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取巡检路线详情"""

    return get_accessible_route_use_case(session, current_user, route_id)


@router.get("/routes/{route_id}/points", response_model=List[InspectionPoint])
def get_route_points(
    route_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取路线的所有巡检点"""

    return list_route_points_use_case(session, current_user, route_id)


@router.put("/routes/{route_id}", response_model=InspectionRoute)
def update_route(
    route_id: int,
    req: RouteUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """更新巡检路线"""

    update_fields = {k: v for k, v in req.model_dump().items() if v is not None}
    return update_inspection_route_use_case(session, current_user, route_id, update_fields)


@router.delete("/routes/{route_id}")
def delete_route(
    route_id: int,
    force: bool = Query(False, description="是否强制删除（同时删除关联的巡检点、计划、任务）"),
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """删除巡检路线（冲突时由全局异常处理器返回 409）"""

    result = delete_inspection_route_use_case(session, current_user, route_id, force)
    return success_response(message=result.message)


@router.post("/points", response_model=InspectionPoint)
def create_point(
    req: PointCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """添加巡检点（路线/设备不存在等由全局异常处理器处理）"""

    return create_inspection_point_use_case(
        session=session,
        current_user=current_user,
        route_id=req.route_id,
        name=req.name,
        device_id=req.device_id,
        location=req.location,
        sequence=req.sequence,
        check_items=req.check_items,
        qr_code=req.qr_code,
        is_required=req.is_required,
    )


@router.put("/points/{point_id}", response_model=InspectionPoint)
def update_point(
    point_id: int,
    req: PointUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """更新巡检点"""

    update_fields = {k: v for k, v in req.model_dump().items() if v is not None}
    return update_inspection_point_use_case(session, current_user, point_id, update_fields)


@router.delete("/points/{point_id}")
def delete_point(
    point_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """删除巡检点"""

    result = delete_inspection_point_use_case(session, current_user, point_id)
    return success_response(message=result.message)


@router.get("/plans", response_model=List[InspectionPlan])
def get_plans(
    is_active: Optional[bool] = Query(None),
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(50, ge=1, le=200, description="每页数量"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取所有巡检计划（支持分页）"""

    return list_accessible_plans_use_case(session, current_user, is_active, offset, limit)


@router.post("/plans", response_model=InspectionPlan)
def create_plan(
    req: PlanCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """创建巡检计划（路线不存在等由全局异常处理器处理）"""

    return create_inspection_plan_use_case(
        session=session,
        current_user=current_user,
        route_id=req.route_id,
        name=req.name,
        plan_type=req.plan_type,
        start_date=req.start_date,
        end_date=req.end_date,
        execution_time=req.execution_time,
        assigned_to=req.assigned_to,
        department=req.department,
    )


@router.get("/plans/{plan_id}", response_model=InspectionPlan)
def get_plan(
    plan_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取巡检计划详情"""

    return get_accessible_plan_use_case(session, current_user, plan_id)


@router.put("/plans/{plan_id}", response_model=InspectionPlan)
def update_plan(
    plan_id: int,
    req: PlanUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """更新巡检计划"""

    update_fields = {k: v for k, v in req.model_dump().items() if v is not None}
    return update_inspection_plan_use_case(session, current_user, plan_id, update_fields)


@router.delete("/plans/{plan_id}")
def delete_plan(
    plan_id: int,
    force: bool = Query(False, description="是否强制删除（取消关联任务的计划关联）"),
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """删除巡检计划（冲突时由全局异常处理器返回 409）"""

    result = delete_inspection_plan_use_case(session, current_user, plan_id, force)
    return success_response(message=result.message)


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

    return list_accessible_tasks_use_case(session, current_user, status, inspector, start_date, end_date, limit)


@router.get("/tasks/today", response_model=List[InspectionTask])
def get_today_tasks(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取今日巡检任务"""

    return list_today_inspection_tasks_use_case(session, current_user)


@router.get("/tasks/pending", response_model=List[InspectionTask])
def get_pending_tasks(
    limit: int = Query(10),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取待执行的巡检任务"""

    return list_pending_inspection_tasks_use_case(session, current_user, limit)


@router.post("/tasks", response_model=InspectionTask)
def create_task(
    req: TaskCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """创建巡检任务（路线/计划不存在等由全局异常处理器处理）"""

    return create_inspection_task_use_case(
        session=session,
        current_user=current_user,
        route_id=req.route_id,
        task_date=req.task_date,
        plan_id=req.plan_id,
        inspector=req.inspector,
    )


@router.get("/tasks/{task_id}", response_model=InspectionTask)
def get_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取巡检任务详情"""

    return get_accessible_task_use_case(session, current_user, task_id)


@router.post("/tasks/{task_id}/start", response_model=InspectionTask)
def start_task(
    task_id: int,
    inspector: Optional[str] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OPERATOR_OR_ADMIN),
):
    """开始执行巡检任务（状态冲突时由全局异常处理器返回 409）"""

    return start_inspection_task_use_case(session, current_user, task_id, inspector)


@router.post("/tasks/{task_id}/complete", response_model=InspectionTask)
def complete_task(
    task_id: int,
    remark: Optional[str] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OPERATOR_OR_ADMIN),
):
    """完成巡检任务（状态冲突时由全局异常处理器返回 409）"""

    return complete_inspection_task_use_case(session, current_user, task_id, remark)


@router.get("/tasks/{task_id}/records", response_model=List[InspectionRecord])
def get_task_records(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取任务的巡检记录"""

    return list_task_records_use_case(session, current_user, task_id)


@router.post("/records", response_model=InspectionRecord)
def submit_record(
    req: RecordSubmitRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OPERATOR_OR_ADMIN),
):
    """提交巡检记录（冲突/状态错误由全局异常处理器返回 409）"""

    return submit_inspection_record_use_case(
        session=session,
        current_user=current_user,
        task_id=req.task_id,
        point_id=req.point_id,
        result=req.result,
        check_details=req.check_details,
        meter_reading=req.meter_reading,
        abnormal_description=req.abnormal_description,
        abnormal_level=req.abnormal_level,
        images=req.images,
        inspector=req.inspector,
    )


@router.get("/statistics")
def get_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取巡检统计信息"""

    stats = get_inspection_statistics_use_case(session, current_user, start_date, end_date)
    return success_response(data=stats)
