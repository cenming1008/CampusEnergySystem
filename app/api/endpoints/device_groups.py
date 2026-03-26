"""
设备分组管理API端点
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.api.deps import MAINTAINER_OR_ADMIN, get_current_user
from app.core.access_control import get_accessible_group_ids
from app.core.audit import audit_log
from app.core.database import get_session
from app.core.exceptions import PermissionDeniedException
from app.core.response import success_response
from app.models.tables import Device, DeviceGroup, User
from app.services.device_group_service import DeviceGroupService

router = APIRouter()


# ==================== 请求/响应模型 ====================

class DeviceGroupCreateRequest(BaseModel):
    """创建分组请求"""
    name: str = Field(..., description="分组名称")
    code: Optional[str] = Field(None, description="分组编码")
    description: Optional[str] = Field(None, description="分组描述")
    group_type: Optional[str] = Field(None, description="分组类型")
    parent_id: Optional[int] = Field(None, description="父分组ID")
    manager: Optional[str] = Field(None, description="负责人")
    contact: Optional[str] = Field(None, description="联系方式")


class DeviceGroupUpdateRequest(BaseModel):
    """更新分组请求"""
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    group_type: Optional[str] = None
    parent_id: Optional[int] = None
    manager: Optional[str] = None
    contact: Optional[str] = None


class AddDeviceRequest(BaseModel):
    """添加设备到分组请求"""
    device_id: int = Field(..., description="设备ID")
    note: Optional[str] = Field(None, description="备注")


class BatchAddDevicesRequest(BaseModel):
    """批量添加设备请求"""
    device_ids: List[int] = Field(..., description="设备ID列表")


# ==================== API端点 ====================

@router.get("/", response_model=List[DeviceGroup])
def get_device_groups(
    group_type: Optional[str] = Query(None, description="按类型筛选"),
    parent_id: Optional[int] = Query(None, description="按父分组ID筛选"),
    is_active: Optional[bool] = Query(None, description="按状态筛选"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    获取设备分组列表
    
    支持筛选条件：
    - group_type: 分组类型（production/office/critical/backup）
    - parent_id: 父分组ID
    - is_active: 是否启用
    """
    groups = DeviceGroupService.get_all_groups(
        session=session,
        group_type=group_type,
        parent_id=parent_id,
        is_active=is_active
    )
    accessible_group_ids = get_accessible_group_ids(session, current_user)
    if accessible_group_ids is None:
        return groups
    return [group for group in groups if group.id in accessible_group_ids]


@router.get("/types")
def get_group_types():
    """
    获取所有支持的分组类型
    
    Returns:
        分组类型列表及说明
    """
    types = [
        {
            "value": "production",
            "label": "生产设备",
            "description": "生产相关的设备"
        },
        {
            "value": "office",
            "label": "办公设备",
            "description": "办公区域的设备"
        },
        {
            "value": "critical",
            "label": "关键设备",
            "description": "需要重点监控的设备"
        },
        {
            "value": "backup",
            "label": "备用设备",
            "description": "备用或待机设备"
        }
    ]
    return success_response(data=types)


@router.get("/search", response_model=List[DeviceGroup])
def search_groups(
    keyword: str = Query(..., description="搜索关键词"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    搜索分组（按名称、编码、描述）
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        匹配的分组列表
    """
    groups = DeviceGroupService.search_groups(session, keyword)
    accessible_group_ids = get_accessible_group_ids(session, current_user)
    if accessible_group_ids is None:
        return groups
    return [group for group in groups if group.id in accessible_group_ids]


@router.get("/statistics")
def get_all_group_statistics(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    获取所有分组的统计信息
    
    Returns:
        所有分组的统计数据（分组名称、设备数量等）
    """
    stats = DeviceGroupService.get_all_group_statistics(session)
    accessible_group_ids = get_accessible_group_ids(session, current_user)
    if accessible_group_ids is not None:
        stats = [item for item in stats if item["id"] in accessible_group_ids]
    return success_response(data=stats)


@router.get("/{group_id}", response_model=DeviceGroup)
def get_group_detail(
    group_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取分组详情（资源不存在时由全局异常处理器返回 404）"""
    accessible_group_ids = get_accessible_group_ids(session, current_user)
    if accessible_group_ids is not None and group_id not in accessible_group_ids:
        raise PermissionDeniedException("当前用户无权访问该分组")
    return DeviceGroupService.get_group_by_id(session, group_id)


@router.post("/", response_model=DeviceGroup)
def create_group(
    request: DeviceGroupCreateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """创建设备分组（父分组不存在等由全局异常处理器处理）"""
    result = DeviceGroupService.create_group(
        session=session,
        name=request.name,
        code=request.code,
        description=request.description,
        group_type=request.group_type,
        parent_id=request.parent_id,
        manager=request.manager,
        contact=request.contact
    )
    audit_log("device_group.create", current_user.username, f"group:{result.id}", role=current_user.role)
    return result


@router.put("/{group_id}", response_model=DeviceGroup)
def update_group(
    group_id: int,
    request: DeviceGroupUpdateRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """更新分组信息（资源不存在等由全局异常处理器处理）"""
    update_data = request.model_dump(exclude_unset=True)
    result = DeviceGroupService.update_group(session, group_id, **update_data)
    audit_log("device_group.update", current_user.username, f"group:{group_id}", role=current_user.role)
    return result


@router.delete("/{group_id}")
def delete_group(
    group_id: int,
    force: bool = Query(False, description="是否强制删除（包括设备关联）"),
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """删除分组（有关联依赖时由全局异常处理器处理）"""
    DeviceGroupService.delete_group(session, group_id, force=force)
    audit_log("device_group.delete", current_user.username, f"group:{group_id}", force=force, role=current_user.role)
    return success_response(message=f"分组 {group_id} 已删除")


# ==================== 设备管理 ====================

@router.get("/{group_id}/devices", response_model=List[Device])
def get_group_devices(
    group_id: int,
    energy_type: Optional[str] = Query(None, description="按能源类型筛选"),
    is_active: Optional[bool] = Query(None, description="按状态筛选"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取分组中的所有设备（分组不存在时由全局异常处理器返回 404）"""
    accessible_group_ids = get_accessible_group_ids(session, current_user)
    if accessible_group_ids is not None and group_id not in accessible_group_ids:
        raise PermissionDeniedException("当前用户无权访问该分组")
    return DeviceGroupService.get_devices_in_group(
        session=session,
        group_id=group_id,
        energy_type=energy_type,
        is_active=is_active
    )


@router.post("/{group_id}/devices")
def add_device_to_group(
    group_id: int,
    request: AddDeviceRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """将设备添加到分组（设备/分组不存在或已在分组中由全局异常处理器处理）"""
    membership = DeviceGroupService.add_device_to_group(
        session=session,
        device_id=request.device_id,
        group_id=group_id,
        note=request.note
    )
    audit_log(
        "device_group.add_device",
        current_user.username,
        f"group:{group_id}",
        device_id=request.device_id,
        role=current_user.role,
    )
    return success_response(
        data={
            "device_id": membership.device_id,
            "group_id": membership.group_id,
            "joined_at": membership.joined_at
        },
        message="设备已添加到分组"
    )


@router.post("/{group_id}/devices/batch")
def batch_add_devices_to_group(
    group_id: int,
    request: BatchAddDevicesRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """批量添加设备到分组（分组不存在等由全局异常处理器处理）"""
    count = DeviceGroupService.batch_add_devices_to_group(
        session=session,
        device_ids=request.device_ids,
        group_id=group_id
    )
    audit_log(
        "device_group.batch_add_devices",
        current_user.username,
        f"group:{group_id}",
        count=count,
        total=len(request.device_ids),
        role=current_user.role,
    )
    return success_response(
        data={"success_count": count, "total": len(request.device_ids)},
        message=f"成功添加 {count}/{len(request.device_ids)} 个设备"
    )


@router.delete("/{group_id}/devices/{device_id}")
def remove_device_from_group(
    group_id: int,
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    """将设备从分组中移除（关联不存在等由全局异常处理器处理）"""
    DeviceGroupService.remove_device_from_group(
        session=session,
        device_id=device_id,
        group_id=group_id
    )
    audit_log(
        "device_group.remove_device",
        current_user.username,
        f"group:{group_id}",
        device_id=device_id,
        role=current_user.role,
    )
    return success_response(message="设备已从分组中移除")


# ==================== 统计分析 ====================

@router.get("/{group_id}/statistics")
def get_group_statistics(
    group_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取分组统计信息（分组不存在时由全局异常处理器返回 404）"""
    accessible_group_ids = get_accessible_group_ids(session, current_user)
    if accessible_group_ids is not None and group_id not in accessible_group_ids:
        raise PermissionDeniedException("当前用户无权访问该分组")
    stats = DeviceGroupService.get_group_statistics(session, group_id)
    return success_response(data=stats)


@router.get("/{group_id}/devices/count")
def get_device_count(
    group_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取分组中的设备数量（分组不存在时由全局异常处理器返回 404）"""
    accessible_group_ids = get_accessible_group_ids(session, current_user)
    if accessible_group_ids is not None and group_id not in accessible_group_ids:
        raise PermissionDeniedException("当前用户无权访问该分组")
    count = DeviceGroupService.get_device_count(session, group_id)
    return success_response(data={"count": count})
