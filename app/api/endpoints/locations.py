"""
位置管理API端点
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import MAINTAINER_OR_ADMIN, get_current_user
from app.core.access_control import (
    ensure_location_access,
    filter_location_tree_by_scope,
    filter_locations_by_scope,
)
from app.core.audit import audit_log
from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import Device, Location, LocationType, User
from app.services.location_service import LocationService

router = APIRouter()


# ==================== 请求/响应模型 ====================

class LocationCreateRequest(BaseModel):
    """创建位置请求"""
    name: str = Field(..., description="位置名称")
    location_type: str = Field(..., description="位置类型")
    parent_id: Optional[int] = Field(None, description="父级位置ID")
    code: Optional[str] = Field(None, description="位置编码")
    description: Optional[str] = Field(None, description="描述")
    area_sqm: Optional[float] = Field(None, description="面积（平方米）")
    manager: Optional[str] = Field(None, description="负责人")
    contact: Optional[str] = Field(None, description="联系方式")


class LocationUpdateRequest(BaseModel):
    """更新位置请求"""
    name: Optional[str] = None
    location_type: Optional[str] = None
    parent_id: Optional[int] = None
    code: Optional[str] = None
    description: Optional[str] = None
    area_sqm: Optional[float] = None
    manager: Optional[str] = None
    contact: Optional[str] = None


class DeviceAssignRequest(BaseModel):
    """设备分配请求"""
    device_id: int = Field(..., description="设备ID")


# ==================== API端点 ====================

@router.get("/", response_model=List[Location])
def get_locations(
    location_type: Optional[str] = Query(None, description="按类型筛选"),
    parent_id: Optional[int] = Query(None, description="按父级ID筛选"),
    is_active: Optional[bool] = Query(None, description="按状态筛选"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    获取位置列表
    
    支持筛选条件：
    - location_type: 位置类型（park/campus/site/building/unit/floor/room/workshop/area/zone）
    - parent_id: 父级位置ID
    - is_active: 是否启用
    """
    locations = LocationService.get_all_locations(
        session=session,
        location_type=location_type,
        parent_id=parent_id,
        is_active=is_active
    )
    return filter_locations_by_scope(locations, current_user)


# 位置类型展示文案（与 models.tables.LocationType 一一对应）
_LOCATION_TYPE_META = {
    LocationType.PARK: ("园区", "最高层园区实体"),
    LocationType.CAMPUS: ("园区组团", "园区/校区/厂区层级"),
    LocationType.SITE: ("站点", "园区下的站点或项目点"),
    LocationType.BUILDING: ("楼栋", "建筑物整体"),
    LocationType.UNIT: ("单元", "楼栋内的单元"),
    LocationType.FLOOR: ("楼层", "单元内的楼层"),
    LocationType.ROOM: ("房间", "具体房间"),
    LocationType.WORKSHOP: ("车间", "生产车间"),
    LocationType.AREA: ("区域", "功能区域"),
    LocationType.ZONE: ("分区", "管理分区"),
}


@router.get("/types")
def get_location_types():
    """
    获取所有支持的位置类型（由 LocationType 枚举生成）
    """
    types = [
        {"value": t.value, "label": _LOCATION_TYPE_META[t][0], "description": _LOCATION_TYPE_META[t][1]}
        for t in LocationType
    ]
    return success_response(data=types)


@router.get("/roots", response_model=List[Location])
def get_root_locations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    获取所有顶级位置（没有父级的位置）
    
    Returns:
        顶级位置列表
    """
    return filter_locations_by_scope(LocationService.get_root_locations(session), current_user)


@router.get("/tree")
def get_location_tree(
    root_id: Optional[int] = Query(None, description="根位置ID（不指定则从顶级开始）"),
    max_depth: Optional[int] = Query(None, description="最大深度"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    获取位置树形结构
    
    Args:
        root_id: 根位置ID（不指定则从顶级开始）
        max_depth: 最大深度（不指定则返回完整树）
        
    Returns:
        树形结构数据
    """
    if root_id is not None:
        ensure_location_access(session, current_user, root_id)
    tree = LocationService.get_location_tree(
        session=session,
        root_location_id=root_id,
        max_depth=max_depth
    )
    return success_response(data=filter_location_tree_by_scope(tree, current_user))


@router.get("/search", response_model=List[Location])
def search_locations(
    keyword: str = Query(..., description="搜索关键词"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    搜索位置（按名称、编码、描述）
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        匹配的位置列表
    """
    return filter_locations_by_scope(LocationService.search_locations(session, keyword), current_user)


@router.get("/{location_id}", response_model=Location)
def get_location_detail(
    location_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    获取位置详情（资源不存在时由全局异常处理器返回 404）
    """
    ensure_location_access(session, current_user, location_id)
    return LocationService.get_location_by_id(session, location_id)


@router.post("/", response_model=Location)
def create_location(
    request: LocationCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """创建位置（业务校验失败由全局异常处理器返回 400/404）"""
    result = LocationService.create_location(
        session=session,
        name=request.name,
        location_type=request.location_type,
        parent_id=request.parent_id,
        code=request.code,
        description=request.description,
        area_sqm=request.area_sqm,
        manager=request.manager,
        contact=request.contact
    )
    audit_log("location.create", current_user.username, f"location:{result.id}", role=current_user.role)
    return result


@router.put("/{location_id}", response_model=Location)
def update_location(
    location_id: int,
    request: LocationUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """更新位置信息（资源不存在等由全局异常处理器处理）"""
    update_data = request.model_dump(exclude_unset=True)
    result = LocationService.update_location(session, location_id, **update_data)
    audit_log("location.update", current_user.username, f"location:{location_id}", role=current_user.role)
    return result


@router.delete("/{location_id}")
def delete_location(
    location_id: int,
    force: bool = Query(False, description="是否强制删除（包括子位置和设备）"),
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """删除位置（依赖冲突等由全局异常处理器处理）"""
    LocationService.delete_location(session, location_id, force=force)
    audit_log("location.delete", current_user.username, f"location:{location_id}", force=force, role=current_user.role)
    return success_response(message=f"位置 {location_id} 已删除")


# ==================== 子位置管理 ====================

@router.get("/{location_id}/children", response_model=List[Location])
def get_child_locations(
    location_id: int,
    recursive: bool = Query(False, description="是否递归获取所有子孙位置"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取子位置（位置不存在时由全局异常处理器返回 404）"""
    ensure_location_access(session, current_user, location_id)
    return filter_locations_by_scope(LocationService.get_child_locations(
        session, location_id, recursive=recursive
    ), current_user)


# ==================== 设备管理 ====================

@router.get("/{location_id}/devices", response_model=List[Device])
def get_location_devices(
    location_id: int,
    recursive: bool = Query(False, description="是否包含子位置的设备"),
    energy_type: Optional[str] = Query(None, description="按能源类型筛选"),
    is_active: Optional[bool] = Query(None, description="按状态筛选"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取位置下的设备（位置不存在时由全局异常处理器返回 404）"""
    ensure_location_access(session, current_user, location_id)
    return LocationService.get_devices_by_location(
        session=session,
        location_id=location_id,
        recursive=recursive,
        energy_type=energy_type,
        is_active=is_active
    )


@router.post("/{location_id}/devices", response_model=Device)
def assign_device_to_location(
    location_id: int,
    request: DeviceAssignRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """将设备分配到位置（设备/位置不存在等由全局异常处理器处理）"""
    result = LocationService.assign_device_to_location(
        session=session,
        device_id=request.device_id,
        location_id=location_id
    )
    audit_log(
        "location.assign_device",
        current_user.username,
        f"location:{location_id}",
        device_id=request.device_id,
        role=current_user.role,
    )
    return result


# ==================== 统计分析 ====================

@router.get("/{location_id}/statistics")
def get_location_statistics(
    location_id: int,
    recursive: bool = Query(True, description="是否包含子位置"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取位置统计信息（位置不存在时由全局异常处理器返回 404）"""
    ensure_location_access(session, current_user, location_id)
    stats = LocationService.get_location_statistics(
        session=session,
        location_id=location_id,
        recursive=recursive
    )
    return success_response(data=stats)
