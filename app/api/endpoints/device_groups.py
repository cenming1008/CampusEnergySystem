"""
设备分组管理API端点
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import DeviceGroup, Device
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
    session: Session = Depends(get_session)
):
    """
    获取设备分组列表
    
    支持筛选条件：
    - group_type: 分组类型（production/office/critical/backup）
    - parent_id: 父分组ID
    - is_active: 是否启用
    """
    return DeviceGroupService.get_all_groups(
        session=session,
        group_type=group_type,
        parent_id=parent_id,
        is_active=is_active
    )


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
    session: Session = Depends(get_session)
):
    """
    搜索分组（按名称、编码、描述）
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        匹配的分组列表
    """
    return DeviceGroupService.search_groups(session, keyword)


@router.get("/statistics")
def get_all_group_statistics(
    session: Session = Depends(get_session)
):
    """
    获取所有分组的统计信息
    
    Returns:
        所有分组的统计数据（分组名称、设备数量等）
    """
    stats = DeviceGroupService.get_all_group_statistics(session)
    return success_response(data=stats)


@router.get("/{group_id}", response_model=DeviceGroup)
def get_group_detail(
    group_id: int,
    session: Session = Depends(get_session)
):
    """
    获取分组详情
    
    Args:
        group_id: 分组ID
        
    Returns:
        分组详情
    """
    try:
        return DeviceGroupService.get_group_by_id(session, group_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=DeviceGroup)
def create_group(
    request: DeviceGroupCreateRequest,
    session: Session = Depends(get_session)
):
    """
    创建设备分组
    
    Args:
        request: 分组创建请求
        
    Returns:
        创建的分组
    """
    try:
        return DeviceGroupService.create_group(
            session=session,
            name=request.name,
            code=request.code,
            description=request.description,
            group_type=request.group_type,
            parent_id=request.parent_id,
            manager=request.manager,
            contact=request.contact
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{group_id}", response_model=DeviceGroup)
def update_group(
    group_id: int,
    request: DeviceGroupUpdateRequest,
    session: Session = Depends(get_session)
):
    """
    更新分组信息
    
    Args:
        group_id: 分组ID
        request: 更新请求
        
    Returns:
        更新后的分组
    """
    try:
        update_data = request.dict(exclude_unset=True)
        return DeviceGroupService.update_group(
            session, group_id, **update_data
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{group_id}")
def delete_group(
    group_id: int,
    force: bool = Query(False, description="是否强制删除（包括设备关联）"),
    session: Session = Depends(get_session)
):
    """
    删除分组
    
    Args:
        group_id: 分组ID
        force: 是否强制删除
        
    Returns:
        成功响应
    """
    try:
        DeviceGroupService.delete_group(session, group_id, force=force)
        return success_response(message=f"分组 {group_id} 已删除")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 设备管理 ====================

@router.get("/{group_id}/devices", response_model=List[Device])
def get_group_devices(
    group_id: int,
    energy_type: Optional[str] = Query(None, description="按能源类型筛选"),
    is_active: Optional[bool] = Query(None, description="按状态筛选"),
    session: Session = Depends(get_session)
):
    """
    获取分组中的所有设备
    
    Args:
        group_id: 分组ID
        energy_type: 能源类型筛选
        is_active: 状态筛选
        
    Returns:
        设备列表
    """
    try:
        return DeviceGroupService.get_devices_in_group(
            session=session,
            group_id=group_id,
            energy_type=energy_type,
            is_active=is_active
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{group_id}/devices")
def add_device_to_group(
    group_id: int,
    request: AddDeviceRequest,
    session: Session = Depends(get_session)
):
    """
    将设备添加到分组
    
    Args:
        group_id: 分组ID
        request: 添加设备请求
        
    Returns:
        成功响应
    """
    try:
        membership = DeviceGroupService.add_device_to_group(
            session=session,
            device_id=request.device_id,
            group_id=group_id,
            note=request.note
        )
        return success_response(
            data={
                "device_id": membership.device_id,
                "group_id": membership.group_id,
                "joined_at": membership.joined_at
            },
            message="设备已添加到分组"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{group_id}/devices/batch")
def batch_add_devices_to_group(
    group_id: int,
    request: BatchAddDevicesRequest,
    session: Session = Depends(get_session)
):
    """
    批量添加设备到分组
    
    Args:
        group_id: 分组ID
        request: 批量添加请求
        
    Returns:
        成功响应（包含成功数量）
    """
    try:
        count = DeviceGroupService.batch_add_devices_to_group(
            session=session,
            device_ids=request.device_ids,
            group_id=group_id
        )
        return success_response(
            data={"success_count": count, "total": len(request.device_ids)},
            message=f"成功添加 {count}/{len(request.device_ids)} 个设备"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{group_id}/devices/{device_id}")
def remove_device_from_group(
    group_id: int,
    device_id: int,
    session: Session = Depends(get_session)
):
    """
    将设备从分组中移除
    
    Args:
        group_id: 分组ID
        device_id: 设备ID
        
    Returns:
        成功响应
    """
    try:
        DeviceGroupService.remove_device_from_group(
            session=session,
            device_id=device_id,
            group_id=group_id
        )
        return success_response(message="设备已从分组中移除")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 统计分析 ====================

@router.get("/{group_id}/statistics")
def get_group_statistics(
    group_id: int,
    session: Session = Depends(get_session)
):
    """
    获取分组统计信息
    
    Args:
        group_id: 分组ID
        
    Returns:
        统计信息（设备数量、按能源类型/类别统计等）
    """
    try:
        stats = DeviceGroupService.get_group_statistics(session, group_id)
        return success_response(data=stats)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{group_id}/devices/count")
def get_device_count(
    group_id: int,
    session: Session = Depends(get_session)
):
    """
    获取分组中的设备数量
    
    Args:
        group_id: 分组ID
        
    Returns:
        设备数量
    """
    try:
        count = DeviceGroupService.get_device_count(session, group_id)
        return success_response(data={"count": count})
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
