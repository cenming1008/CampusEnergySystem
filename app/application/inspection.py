"""
巡检主流程 use case。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlmodel import Session

from app.core.access_control import (
    ensure_device_access,
    ensure_route_access,
    get_accessible_plan_ids,
    get_accessible_route_ids,
    get_accessible_task_ids,
    get_allowed_device_ids,
)
from app.core.audit import audit_log
from app.models.tables import InspectionPoint, User
from app.services.inspection_service import InspectionService


@dataclass(frozen=True)
class InspectionActionResult:
    message: str


def list_accessible_routes_use_case(
    session: Session,
    current_user: User,
    is_active: Optional[bool] = None,
    offset: int = 0,
    limit: int = 50,
):
    routes = InspectionService.get_all_routes(session, is_active, offset, limit)
    accessible_route_ids = get_accessible_route_ids(session, current_user)
    if accessible_route_ids is None:
        return routes
    return [route for route in routes if route.id in accessible_route_ids]


def create_inspection_route_use_case(
    session: Session,
    current_user: User,
    name: str,
    code: Optional[str] = None,
    description: Optional[str] = None,
    estimated_duration: int = 30,
):
    route = InspectionService.create_route(
        session=session,
        name=name,
        code=code,
        description=description,
        estimated_duration=estimated_duration,
    )
    audit_log("inspection.route.create", current_user.username, f"route:{route.id}", role=current_user.role)
    return route


def get_accessible_route_use_case(
    session: Session,
    current_user: User,
    route_id: int,
):
    ensure_route_access(session, current_user, route_id)
    return InspectionService.get_route_by_id(session, route_id)


def list_route_points_use_case(
    session: Session,
    current_user: User,
    route_id: int,
):
    ensure_route_access(session, current_user, route_id)
    points = InspectionService.get_route_points(session, route_id)
    allowed_device_ids = get_allowed_device_ids(session, current_user)
    if allowed_device_ids is None:
        return points
    return [
        point for point in points
        if point.device_id is None or point.device_id in allowed_device_ids
    ]


def update_inspection_route_use_case(
    session: Session,
    current_user: User,
    route_id: int,
    update_fields: dict,
):
    ensure_route_access(session, current_user, route_id)
    route = InspectionService.update_route(session, route_id, **update_fields)
    audit_log("inspection.route.update", current_user.username, f"route:{route_id}", role=current_user.role)
    return route


def delete_inspection_route_use_case(
    session: Session,
    current_user: User,
    route_id: int,
    force: bool = False,
) -> InspectionActionResult:
    ensure_route_access(session, current_user, route_id)
    InspectionService.delete_route(session, route_id, force=force)
    audit_log("inspection.route.delete", current_user.username, f"route:{route_id}", force=force, role=current_user.role)
    return InspectionActionResult(message="删除成功")


def create_inspection_point_use_case(
    session: Session,
    current_user: User,
    route_id: int,
    name: str,
    device_id: Optional[int] = None,
    location: Optional[str] = None,
    sequence: int = 0,
    check_items: Optional[list[str]] = None,
    qr_code: Optional[str] = None,
    is_required: bool = True,
):
    ensure_route_access(session, current_user, route_id)
    if device_id is not None:
        ensure_device_access(session, current_user, device_id)
    point = InspectionService.add_point_to_route(
        session=session,
        route_id=route_id,
        name=name,
        device_id=device_id,
        location=location,
        sequence=sequence,
        check_items=check_items,
        qr_code=qr_code,
        is_required=is_required,
    )
    audit_log("inspection.point.create", current_user.username, f"route:{route_id}", role=current_user.role)
    return point


def update_inspection_point_use_case(
    session: Session,
    current_user: User,
    point_id: int,
    update_fields: dict,
):
    point = session.get(InspectionPoint, point_id)
    if point is not None:
        ensure_route_access(session, current_user, point.route_id)
    if (device_id := update_fields.get("device_id")) is not None:
        ensure_device_access(session, current_user, device_id)
    result = InspectionService.update_point(session, point_id, **update_fields)
    audit_log("inspection.point.update", current_user.username, f"point:{point_id}", role=current_user.role)
    return result


def delete_inspection_point_use_case(
    session: Session,
    current_user: User,
    point_id: int,
) -> InspectionActionResult:
    point = session.get(InspectionPoint, point_id)
    if point is not None:
        ensure_route_access(session, current_user, point.route_id)
    InspectionService.delete_point(session, point_id)
    audit_log("inspection.point.delete", current_user.username, f"point:{point_id}", role=current_user.role)
    return InspectionActionResult(message="删除成功")


def list_accessible_plans_use_case(
    session: Session,
    current_user: User,
    is_active: Optional[bool] = None,
    offset: int = 0,
    limit: int = 50,
):
    plans = InspectionService.get_all_plans(session, is_active, offset, limit)
    accessible_plan_ids = get_accessible_plan_ids(session, current_user)
    if accessible_plan_ids is None:
        return plans
    return [plan for plan in plans if plan.id in accessible_plan_ids]


def create_inspection_plan_use_case(
    session: Session,
    current_user: User,
    route_id: int,
    name: str,
    plan_type: str = "daily",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    execution_time: str = "08:00",
    assigned_to: Optional[str] = None,
    department: Optional[str] = None,
):
    ensure_route_access(session, current_user, route_id)
    plan = InspectionService.create_plan(
        session=session,
        route_id=route_id,
        name=name,
        plan_type=plan_type,
        start_date=start_date,
        end_date=end_date,
        execution_time=execution_time,
        assigned_to=assigned_to,
        department=department,
    )
    audit_log("inspection.plan.create", current_user.username, f"route:{route_id}", role=current_user.role)
    return plan


def get_accessible_plan_use_case(
    session: Session,
    current_user: User,
    plan_id: int,
):
    plan = InspectionService.get_plan_by_id(session, plan_id)
    accessible_plan_ids = get_accessible_plan_ids(session, current_user)
    if accessible_plan_ids is not None and plan_id not in accessible_plan_ids:
        ensure_route_access(session, current_user, plan.route_id)
    return plan


def update_inspection_plan_use_case(
    session: Session,
    current_user: User,
    plan_id: int,
    update_fields: dict,
):
    plan = InspectionService.get_plan_by_id(session, plan_id)
    ensure_route_access(session, current_user, plan.route_id)
    if (route_id := update_fields.get("route_id")) is not None:
        ensure_route_access(session, current_user, route_id)
    result = InspectionService.update_plan(session, plan_id, **update_fields)
    audit_log("inspection.plan.update", current_user.username, f"plan:{plan_id}", role=current_user.role)
    return result


def delete_inspection_plan_use_case(
    session: Session,
    current_user: User,
    plan_id: int,
    force: bool = False,
) -> InspectionActionResult:
    plan = InspectionService.get_plan_by_id(session, plan_id)
    ensure_route_access(session, current_user, plan.route_id)
    InspectionService.delete_plan(session, plan_id, force=force)
    audit_log("inspection.plan.delete", current_user.username, f"plan:{plan_id}", force=force, role=current_user.role)
    return InspectionActionResult(message="删除成功")


def list_accessible_tasks_use_case(
    session: Session,
    current_user: User,
    status: Optional[str] = None,
    inspector: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 50,
):
    return InspectionService.get_tasks(
        session=session,
        status=status,
        inspector=inspector,
        start_date=start_date,
        end_date=end_date,
        allowed_route_ids=get_accessible_route_ids(session, current_user),
        limit=limit,
    )


def list_today_inspection_tasks_use_case(
    session: Session,
    current_user: User,
):
    return InspectionService.get_today_tasks(
        session,
        allowed_route_ids=get_accessible_route_ids(session, current_user),
    )


def list_pending_inspection_tasks_use_case(
    session: Session,
    current_user: User,
    limit: int = 10,
):
    return InspectionService.get_pending_tasks(
        session,
        limit,
        allowed_route_ids=get_accessible_route_ids(session, current_user),
    )


def create_inspection_task_use_case(
    session: Session,
    current_user: User,
    route_id: int,
    task_date: Optional[datetime] = None,
    plan_id: Optional[int] = None,
    inspector: Optional[str] = None,
):
    ensure_route_access(session, current_user, route_id)
    task = InspectionService.create_task(
        session=session,
        route_id=route_id,
        task_date=task_date,
        plan_id=plan_id,
        inspector=inspector,
    )
    audit_log("inspection.task.create", current_user.username, f"route:{route_id}", role=current_user.role)
    return task


def get_accessible_task_use_case(
    session: Session,
    current_user: User,
    task_id: int,
):
    task = InspectionService.get_task_by_id(session, task_id)
    accessible_task_ids = get_accessible_task_ids(session, current_user)
    if accessible_task_ids is not None and task_id not in accessible_task_ids:
        ensure_route_access(session, current_user, task.route_id)
    return task


def start_inspection_task_use_case(
    session: Session,
    current_user: User,
    task_id: int,
    inspector: Optional[str] = None,
):
    task = InspectionService.get_task_by_id(session, task_id)
    ensure_route_access(session, current_user, task.route_id)
    result = InspectionService.start_task(session, task_id, inspector or current_user.username)
    audit_log("inspection.task.start", current_user.username, f"task:{task_id}", role=current_user.role)
    return result


def complete_inspection_task_use_case(
    session: Session,
    current_user: User,
    task_id: int,
    remark: Optional[str] = None,
):
    task = InspectionService.get_task_by_id(session, task_id)
    ensure_route_access(session, current_user, task.route_id)
    result = InspectionService.complete_task(session, task_id, remark)
    audit_log("inspection.task.complete", current_user.username, f"task:{task_id}", remark=remark, role=current_user.role)
    return result


def list_task_records_use_case(
    session: Session,
    current_user: User,
    task_id: int,
):
    task = InspectionService.get_task_by_id(session, task_id)
    ensure_route_access(session, current_user, task.route_id)
    return InspectionService.get_task_records(session, task_id)


def submit_inspection_record_use_case(
    session: Session,
    current_user: User,
    task_id: int,
    point_id: int,
    result: str = "normal",
    check_details: Optional[dict] = None,
    meter_reading: Optional[float] = None,
    abnormal_description: Optional[str] = None,
    abnormal_level: Optional[str] = None,
    images: Optional[list[str]] = None,
    inspector: Optional[str] = None,
):
    task = InspectionService.get_task_by_id(session, task_id)
    ensure_route_access(session, current_user, task.route_id)
    point = session.get(InspectionPoint, point_id)
    if point is not None and point.device_id is not None:
        ensure_device_access(session, current_user, point.device_id)
    record = InspectionService.submit_inspection_record(
        session=session,
        task_id=task_id,
        point_id=point_id,
        result=result,
        check_details=check_details,
        meter_reading=meter_reading,
        abnormal_description=abnormal_description,
        abnormal_level=abnormal_level,
        images=images,
        inspector=inspector or current_user.username,
    )
    audit_log("inspection.record.submit", current_user.username, f"task:{task_id}", point_id=point_id, role=current_user.role)
    return record


def get_inspection_statistics_use_case(
    session: Session,
    current_user: User,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    return InspectionService.get_inspection_statistics(
        session=session,
        start_date=start_date,
        end_date=end_date,
        allowed_route_ids=get_accessible_route_ids(session, current_user),
    )
