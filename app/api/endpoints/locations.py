"""
位置管理API端点
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session

from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import Location, Device, LocationType
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
    session: Session = Depends(get_session)
):
    """
    获取位置列表
    
    支持筛选条件：
    - location_type: 位置类型（building/unit/floor/room/workshop/area/zone）
    - parent_id: 父级位置ID
    - is_active: 是否启用
    """
    return LocationService.get_all_locations(
        session=session,
        location_type=location_type,
        parent_id=parent_id,
        is_active=is_active
    )


@router.get("/types")
def get_location_types():
    """
    获取所有支持的位置类型
    
    Returns:
        位置类型列表及说明
    """
    types = [
        {
            "value": LocationType.BUILDING,
            "label": "楼栋",
            "description": "建筑物整体"
        },
        {
            "value": LocationType.UNIT,
            "label": "单元",
            "description": "楼栋内的单元"
        },
        {
            "value": LocationType.FLOOR,
            "label": "楼层",
            "description": "单元内的楼层"
        },
        {
            "value": LocationType.ROOM,
            "label": "房间",
            "description": "具体房间"
        },
        {
            "value": LocationType.WORKSHOP,
            "label": "车间",
            "description": "生产车间"
        },
        {
            "value": LocationType.AREA,
            "label": "区域",
            "description": "功能区域"
        },
        {
            "value": LocationType.ZONE,
            "label": "分区",
            "description": "管理分区"
        }
    ]
    return success_response(data=types)


@router.get("/roots", response_model=List[Location])
def get_root_locations(session: Session = Depends(get_session)):
    """
    获取所有顶级位置（没有父级的位置）
    
    Returns:
        顶级位置列表
    """
    return LocationService.get_root_locations(session)


@router.get("/tree")
def get_location_tree(
    root_id: Optional[int] = Query(None, description="根位置ID（不指定则从顶级开始）"),
    max_depth: Optional[int] = Query(None, description="最大深度"),
    session: Session = Depends(get_session)
):
    """
    获取位置树形结构
    
    Args:
        root_id: 根位置ID（不指定则从顶级开始）
        max_depth: 最大深度（不指定则返回完整树）
        
    Returns:
        树形结构数据
    """
    tree = LocationService.get_location_tree(
        session=session,
        root_location_id=root_id,
        max_depth=max_depth
    )
    return success_response(data=tree)


@router.get("/search", response_model=List[Location])
def search_locations(
    keyword: str = Query(..., description="搜索关键词"),
    session: Session = Depends(get_session)
):
    """
    搜索位置（按名称、编码、描述）
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        匹配的位置列表
    """
    return LocationService.search_locations(session, keyword)


@router.get("/{location_id}", response_model=Location)
def get_location_detail(
    location_id: int,
    session: Session = Depends(get_session)
):
    """
    获取位置详情
    
    Args:
        location_id: 位置ID
        
    Returns:
        位置详情
    """
    try:
        return LocationService.get_location_by_id(session, location_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/", response_model=Location)
def create_location(
    request: LocationCreateRequest,
    session: Session = Depends(get_session)
):
    """
    创建位置
    
    Args:
        request: 位置创建请求
        
    Returns:
        创建的位置
    """
    try:
        return LocationService.create_location(
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
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{location_id}", response_model=Location)
def update_location(
    location_id: int,
    request: LocationUpdateRequest,
    session: Session = Depends(get_session)
):
    """
    更新位置信息
    
    Args:
        location_id: 位置ID
        request: 更新请求
        
    Returns:
        更新后的位置
    """
    try:
        update_data = request.dict(exclude_unset=True)
        return LocationService.update_location(
            session, location_id, **update_data
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{location_id}")
def delete_location(
    location_id: int,
    force: bool = Query(False, description="是否强制删除（包括子位置和设备）"),
    session: Session = Depends(get_session)
):
    """
    删除位置
    
    Args:
        location_id: 位置ID
        force: 是否强制删除
        
    Returns:
        成功响应
    """
    try:
        LocationService.delete_location(session, location_id, force=force)
        return success_response(message=f"位置 {location_id} 已删除")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 子位置管理 ====================

@router.get("/{location_id}/children", response_model=List[Location])
def get_child_locations(
    location_id: int,
    recursive: bool = Query(False, description="是否递归获取所有子孙位置"),
    session: Session = Depends(get_session)
):
    """
    获取子位置
    
    Args:
        location_id: 父级位置ID
        recursive: 是否递归获取所有子孙位置
        
    Returns:
        子位置列表
    """
    try:
        return LocationService.get_child_locations(
            session, location_id, recursive=recursive
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# ==================== 设备管理 ====================

@router.get("/{location_id}/devices", response_model=List[Device])
def get_location_devices(
    location_id: int,
    recursive: bool = Query(False, description="是否包含子位置的设备"),
    energy_type: Optional[str] = Query(None, description="按能源类型筛选"),
    is_active: Optional[bool] = Query(None, description="按状态筛选"),
    session: Session = Depends(get_session)
):
    """
    获取位置下的设备
    
    Args:
        location_id: 位置ID
        recursive: 是否包含子位置的设备
        energy_type: 能源类型筛选
        is_active: 状态筛选
        
    Returns:
        设备列表
    """
    try:
        return LocationService.get_devices_by_location(
            session=session,
            location_id=location_id,
            recursive=recursive,
            energy_type=energy_type,
            is_active=is_active
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{location_id}/devices", response_model=Device)
def assign_device_to_location(
    location_id: int,
    request: DeviceAssignRequest,
    session: Session = Depends(get_session)
):
    """
    将设备分配到位置
    
    Args:
        location_id: 位置ID
        request: 设备分配请求
        
    Returns:
        更新后的设备
    """
    try:
        return LocationService.assign_device_to_location(
            session=session,
            device_id=request.device_id,
            location_id=location_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== 统计分析 ====================

@router.get("/{location_id}/statistics")
def get_location_statistics(
    location_id: int,
    recursive: bool = Query(True, description="是否包含子位置"),
    session: Session = Depends(get_session)
):
    """
    获取位置统计信息
    
    Args:
        location_id: 位置ID
        recursive: 是否包含子位置
        
    Returns:
        统计信息（设备数量、按能源类型/类别统计等）
    """
    try:
        stats = LocationService.get_location_statistics(
            session=session,
            location_id=location_id,
            recursive=recursive
        )
        return success_response(data=stats)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
