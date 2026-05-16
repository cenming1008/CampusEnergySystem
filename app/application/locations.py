"""
位置管理主流程 use case。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlmodel import Session

from app.core.access_control import (
    ensure_location_access,
    filter_location_tree_by_scope,
    filter_locations_by_scope,
)
from app.core.audit import audit_log
from app.models.tables import Device, Location, User
from app.services.location_service import LocationService


@dataclass(frozen=True)
class LocationActionResult:
    message: str


def list_locations_use_case(
    session: Session,
    current_user: User,
    location_type: Optional[str] = None,
    parent_id: Optional[int] = None,
    is_active: Optional[bool] = None,
) -> list[Location]:
    locations = LocationService.get_all_locations(
        session=session,
        location_type=location_type,
        parent_id=parent_id,
        is_active=is_active,
    )
    return filter_locations_by_scope(locations, current_user)


def list_root_locations_use_case(session: Session, current_user: User) -> list[Location]:
    return filter_locations_by_scope(LocationService.get_root_locations(session), current_user)


def get_location_tree_use_case(
    session: Session,
    current_user: User,
    root_id: Optional[int] = None,
    max_depth: Optional[int] = None,
) -> list[dict]:
    if root_id is not None:
        ensure_location_access(session, current_user, root_id)
    tree = LocationService.get_location_tree(
        session=session,
        root_location_id=root_id,
        max_depth=max_depth,
    )
    return filter_location_tree_by_scope(tree, current_user)


def search_locations_use_case(
    session: Session,
    current_user: User,
    keyword: str,
) -> list[Location]:
    return filter_locations_by_scope(LocationService.search_locations(session, keyword), current_user)


def get_location_detail_use_case(
    session: Session,
    current_user: User,
    location_id: int,
) -> Location:
    ensure_location_access(session, current_user, location_id)
    return LocationService.get_location_by_id(session, location_id)


def create_location_use_case(
    session: Session,
    current_user: User,
    name: str,
    location_type: str,
    parent_id: Optional[int] = None,
    code: Optional[str] = None,
    description: Optional[str] = None,
    area_sqm: Optional[float] = None,
    manager: Optional[str] = None,
    contact: Optional[str] = None,
) -> Location:
    result = LocationService.create_location(
        session=session,
        name=name,
        location_type=location_type,
        parent_id=parent_id,
        code=code,
        description=description,
        area_sqm=area_sqm,
        manager=manager,
        contact=contact,
    )
    audit_log("location.create", current_user.username, f"location:{result.id}", role=current_user.role)
    return result


def update_location_use_case(
    session: Session,
    current_user: User,
    location_id: int,
    update_data: dict,
) -> Location:
    result = LocationService.update_location(session, location_id, **update_data)
    audit_log("location.update", current_user.username, f"location:{location_id}", role=current_user.role)
    return result


def delete_location_use_case(
    session: Session,
    current_user: User,
    location_id: int,
    force: bool = False,
) -> LocationActionResult:
    LocationService.delete_location(session, location_id, force=force)
    audit_log(
        "location.delete",
        current_user.username,
        f"location:{location_id}",
        force=force,
        role=current_user.role,
    )
    return LocationActionResult(message=f"位置 {location_id} 已删除")


def list_child_locations_use_case(
    session: Session,
    current_user: User,
    location_id: int,
    recursive: bool = False,
) -> list[Location]:
    ensure_location_access(session, current_user, location_id)
    children = LocationService.get_child_locations(session, location_id, recursive=recursive)
    return filter_locations_by_scope(children, current_user)


def list_location_devices_use_case(
    session: Session,
    current_user: User,
    location_id: int,
    recursive: bool = False,
    energy_type: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> list[Device]:
    ensure_location_access(session, current_user, location_id)
    return LocationService.get_devices_by_location(
        session=session,
        location_id=location_id,
        recursive=recursive,
        energy_type=energy_type,
        is_active=is_active,
    )


def assign_device_to_location_use_case(
    session: Session,
    current_user: User,
    location_id: int,
    device_id: int,
) -> Device:
    result = LocationService.assign_device_to_location(
        session=session,
        device_id=device_id,
        location_id=location_id,
    )
    audit_log(
        "location.assign_device",
        current_user.username,
        f"location:{location_id}",
        device_id=device_id,
        role=current_user.role,
    )
    return result


def get_location_statistics_use_case(
    session: Session,
    current_user: User,
    location_id: int,
    recursive: bool = True,
) -> dict:
    ensure_location_access(session, current_user, location_id)
    return LocationService.get_location_statistics(
        session=session,
        location_id=location_id,
        recursive=recursive,
    )
