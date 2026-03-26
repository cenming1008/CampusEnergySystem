"""
数据范围权限控制。
"""

from __future__ import annotations

from typing import Iterable

from sqlmodel import Session, select

from app.core.exceptions import PermissionDeniedException
from app.models.tables import (
    Device,
    DeviceGroupMembership,
    InspectionPlan,
    InspectionPoint,
    InspectionRoute,
    InspectionTask,
    Location,
    User,
    UserRole,
)


def parse_location_scope(user: User) -> set[int] | None:
    """解析用户的位置范围；None 表示不限制。"""
    if user.role == UserRole.ADMIN:
        return None

    raw_value = getattr(user, "location_scope", None)
    if not raw_value:
        return None

    values: set[int] = set()
    for item in str(raw_value).split(","):
        item = item.strip()
        if not item:
            continue
        try:
            values.add(int(item))
        except ValueError:
            continue
    return values or None


def filter_devices_by_scope(devices: Iterable[Device], user: User) -> list[Device]:
    """按位置范围过滤设备列表。"""
    allowed_location_ids = parse_location_scope(user)
    if allowed_location_ids is None:
        return list(devices)
    return [device for device in devices if device.location_id in allowed_location_ids]


def ensure_device_access(session: Session, user: User, device_id: int) -> Device:
    """校验用户是否可访问指定设备。"""
    device = session.get(Device, device_id)
    if not device:
        raise PermissionDeniedException("设备不存在或不可访问")

    allowed_location_ids = parse_location_scope(user)
    if allowed_location_ids is None:
        return device

    if device.location_id not in allowed_location_ids:
        raise PermissionDeniedException("当前用户无权访问该设备")
    return device


def get_allowed_device_ids(session: Session, user: User) -> set[int] | None:
    """获取用户在其位置范围内可访问的设备ID集合；None 表示不限制。"""
    allowed_location_ids = parse_location_scope(user)
    if allowed_location_ids is None:
        return None

    statement = select(Device.id).where(Device.location_id.in_(allowed_location_ids))
    return {row for row in session.exec(statement).all()}


def filter_locations_by_scope(locations: Iterable[Location], user: User) -> list[Location]:
    """按位置范围过滤位置列表。"""
    allowed_location_ids = parse_location_scope(user)
    if allowed_location_ids is None:
        return list(locations)
    return [location for location in locations if location.id in allowed_location_ids]


def ensure_location_access(session: Session, user: User, location_id: int) -> Location:
    """校验用户是否可访问指定位置。"""
    location = session.get(Location, location_id)
    if not location:
        raise PermissionDeniedException("位置不存在或不可访问")

    allowed_location_ids = parse_location_scope(user)
    if allowed_location_ids is None:
        return location
    if location.id not in allowed_location_ids:
        raise PermissionDeniedException("当前用户无权访问该位置")
    return location


def get_accessible_group_ids(session: Session, user: User) -> set[int] | None:
    """获取用户在其位置范围内可访问的设备分组ID集合；None 表示不限制。"""
    allowed_location_ids = parse_location_scope(user)
    if allowed_location_ids is None:
        return None

    statement = (
        select(DeviceGroupMembership.group_id)
        .join(Device, Device.id == DeviceGroupMembership.device_id)
        .where(Device.location_id.in_(allowed_location_ids))
    )
    return {row for row in session.exec(statement).all()}


def filter_location_tree_by_scope(tree: list[dict], user: User) -> list[dict]:
    """按位置范围过滤树形节点，保留有可见后代的祖先。"""
    allowed_location_ids = parse_location_scope(user)
    if allowed_location_ids is None:
        return tree

    def filter_node(node: dict) -> dict | None:
        children = [filtered for child in node.get("children", []) if (filtered := filter_node(child))]
        if node.get("id") in allowed_location_ids or children:
            copied = dict(node)
            copied["children"] = children
            return copied
        return None

    return [filtered for node in tree if (filtered := filter_node(node))]


def get_accessible_route_ids(session: Session, user: User) -> set[int] | None:
    """获取用户可访问的巡检路线 ID 集合；None 表示不限制。"""
    allowed_location_ids = parse_location_scope(user)
    if allowed_location_ids is None:
        return None

    statement = (
        select(InspectionPoint.route_id)
        .join(Device, Device.id == InspectionPoint.device_id)
        .where(Device.location_id.in_(allowed_location_ids))
    )
    return {row for row in session.exec(statement).all()}


def ensure_route_access(session: Session, user: User, route_id: int) -> InspectionRoute:
    """校验用户是否可访问指定巡检路线。"""
    route = session.get(InspectionRoute, route_id)
    if not route:
        raise PermissionDeniedException("巡检路线不存在或不可访问")

    accessible_route_ids = get_accessible_route_ids(session, user)
    if accessible_route_ids is None:
        return route
    if route_id not in accessible_route_ids:
        raise PermissionDeniedException("当前用户无权访问该巡检路线")
    return route


def get_accessible_plan_ids(session: Session, user: User) -> set[int] | None:
    """获取用户可访问的巡检计划 ID 集合；None 表示不限制。"""
    accessible_route_ids = get_accessible_route_ids(session, user)
    if accessible_route_ids is None:
        return None
    if not accessible_route_ids:
        return set()

    statement = select(InspectionPlan.id).where(InspectionPlan.route_id.in_(accessible_route_ids))
    return {row for row in session.exec(statement).all()}


def get_accessible_task_ids(session: Session, user: User) -> set[int] | None:
    """获取用户可访问的巡检任务 ID 集合；None 表示不限制。"""
    accessible_route_ids = get_accessible_route_ids(session, user)
    if accessible_route_ids is None:
        return None
    if not accessible_route_ids:
        return set()

    statement = select(InspectionTask.id).where(InspectionTask.route_id.in_(accessible_route_ids))
    return {row for row in session.exec(statement).all()}
