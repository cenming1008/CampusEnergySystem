"""
设备维护管理服务层
封装设备维护相关的业务逻辑
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlmodel import Session, select, func, or_, and_
from app.core.logger import logger

from app.models.tables import (
    DeviceMaintenance, 
    Device, 
    MaintenanceType, 
    MaintenanceStatus
)
from app.core.exceptions import ResourceNotFoundException, DatabaseException


class MaintenanceService:
    """
    设备维护管理服务类
    
    提供设备维护相关的业务逻辑，包括：
    - 创建和管理维护记录
    - 查询维护历史
    - 维护统计和提醒
    - 维护成本分析
    """
    
    # ==================== 维护记录管理 ====================
    
    @staticmethod
    def create_maintenance(
        session: Session,
        device_id: int,
        maintenance_type: str,
        scheduled_time: datetime,
        title: str,
        description: Optional[str] = None,
        operator: Optional[str] = None,
        created_by: Optional[str] = None,
        **extra_fields
    ) -> DeviceMaintenance:
        """
        创建维护记录
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            maintenance_type: 维护类型
            scheduled_time: 计划维护时间
            title: 维护标题
            description: 维护描述
            operator: 维护人员
            created_by: 创建人
            **extra_fields: 其他字段
            
        Returns:
            创建的维护记录
            
        Raises:
            ResourceNotFoundException: 设备不存在
        """
        # 验证设备是否存在
        device = session.get(Device, device_id)
        if not device:
            raise ResourceNotFoundException("设备", device_id)
        
        # 验证维护类型
        valid_types = [t.value for t in MaintenanceType]
        if maintenance_type not in valid_types:
            raise ValueError(
                f"无效的维护类型: {maintenance_type}。"
                f"有效值: {', '.join(valid_types)}"
            )
        
        # 创建维护记录
        maintenance = DeviceMaintenance(
            device_id=device_id,
            maintenance_type=maintenance_type,
            scheduled_time=scheduled_time,
            title=title,
            description=description,
            operator=operator,
            created_by=created_by,
            status=MaintenanceStatus.SCHEDULED,
            **extra_fields
        )
        
        session.add(maintenance)
        session.commit()
        session.refresh(maintenance)
        
        logger.info(
            f"创建维护记录: device_id={device_id}, "
            f"type={maintenance_type}, id={maintenance.id}"
        )
        
        return maintenance
    
    @staticmethod
    def get_maintenance_by_id(
        session: Session, 
        maintenance_id: int
    ) -> DeviceMaintenance:
        """
        根据ID获取维护记录
        
        Args:
            session: 数据库会话
            maintenance_id: 维护记录ID
            
        Returns:
            维护记录
            
        Raises:
            ResourceNotFoundException: 记录不存在
        """
        maintenance = session.get(DeviceMaintenance, maintenance_id)
        if not maintenance:
            raise ResourceNotFoundException("维护记录", maintenance_id)
        return maintenance
    
    @staticmethod
    def get_maintenance_list(
        session: Session,
        device_id: Optional[int] = None,
        maintenance_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[DeviceMaintenance]:
        """
        获取维护记录列表（支持多条件筛选）
        
        Args:
            session: 数据库会话
            device_id: 设备ID筛选
            maintenance_type: 维护类型筛选
            status: 状态筛选
            start_date: 开始日期筛选
            end_date: 结束日期筛选
            limit: 返回记录数限制
            offset: 分页偏移量
            
        Returns:
            维护记录列表
        """
        statement = select(DeviceMaintenance)
        
        # 应用筛选条件
        if device_id:
            statement = statement.where(DeviceMaintenance.device_id == device_id)
        
        if maintenance_type:
            statement = statement.where(
                DeviceMaintenance.maintenance_type == maintenance_type
            )
        
        if status:
            statement = statement.where(DeviceMaintenance.status == status)
        
        if start_date:
            statement = statement.where(
                DeviceMaintenance.scheduled_time >= start_date
            )
        
        if end_date:
            statement = statement.where(
                DeviceMaintenance.scheduled_time <= end_date
            )
        
        # 排序和分页
        statement = (
            statement
            .order_by(DeviceMaintenance.scheduled_time.desc())
            .limit(limit)
            .offset(offset)
        )
        
        return list(session.exec(statement).all())
    
    @staticmethod
    def update_maintenance(
        session: Session,
        maintenance_id: int,
        **update_fields
    ) -> DeviceMaintenance:
        """
        更新维护记录
        
        Args:
            session: 数据库会话
            maintenance_id: 维护记录ID
            **update_fields: 要更新的字段
            
        Returns:
            更新后的维护记录
            
        Raises:
            ResourceNotFoundException: 记录不存在
        """
        maintenance = MaintenanceService.get_maintenance_by_id(
            session, maintenance_id
        )
        
        # 更新字段
        for field, value in update_fields.items():
            if hasattr(maintenance, field) and value is not None:
                setattr(maintenance, field, value)
        
        # 更新修改时间
        maintenance.updated_at = datetime.now()
        
        session.add(maintenance)
        session.commit()
        session.refresh(maintenance)
        
        logger.info(f"更新维护记录: id={maintenance_id}")
        
        return maintenance
    
    @staticmethod
    def start_maintenance(
        session: Session,
        maintenance_id: int,
        operator: Optional[str] = None
    ) -> DeviceMaintenance:
        """
        开始维护（将状态改为进行中）
        
        Args:
            session: 数据库会话
            maintenance_id: 维护记录ID
            operator: 维护人员
            
        Returns:
            更新后的维护记录
        """
        update_data = {
            "status": MaintenanceStatus.IN_PROGRESS,
            "actual_start_time": datetime.now()
        }
        
        if operator:
            update_data["operator"] = operator
        
        return MaintenanceService.update_maintenance(
            session, maintenance_id, **update_data
        )
    
    @staticmethod
    def complete_maintenance(
        session: Session,
        maintenance_id: int,
        result: Optional[str] = None,
        cost: Optional[float] = None,
        parts_replaced: Optional[str] = None,
        next_maintenance_date: Optional[datetime] = None
    ) -> DeviceMaintenance:
        """
        完成维护（将状态改为已完成）
        
        Args:
            session: 数据库会话
            maintenance_id: 维护记录ID
            result: 维护结果/备注
            cost: 维护成本
            parts_replaced: 更换的部件（JSON字符串）
            next_maintenance_date: 建议下次维护日期
            
        Returns:
            更新后的维护记录
        """
        maintenance = MaintenanceService.get_maintenance_by_id(
            session, maintenance_id
        )
        
        # 计算维护时长
        duration_minutes = None
        if maintenance.actual_start_time:
            end_time = datetime.now()
            duration = end_time - maintenance.actual_start_time
            duration_minutes = int(duration.total_seconds() / 60)
        
        update_data = {
            "status": MaintenanceStatus.COMPLETED,
            "actual_end_time": datetime.now(),
            "duration_minutes": duration_minutes,
            "result": result,
            "cost": cost,
            "parts_replaced": parts_replaced,
            "next_maintenance_date": next_maintenance_date
        }
        
        return MaintenanceService.update_maintenance(
            session, maintenance_id, **update_data
        )
    
    @staticmethod
    def cancel_maintenance(
        session: Session,
        maintenance_id: int,
        reason: Optional[str] = None
    ) -> DeviceMaintenance:
        """
        取消维护
        
        Args:
            session: 数据库会话
            maintenance_id: 维护记录ID
            reason: 取消原因
            
        Returns:
            更新后的维护记录
        """
        update_data = {
            "status": MaintenanceStatus.CANCELLED
        }
        
        if reason:
            update_data["result"] = f"取消原因: {reason}"
        
        return MaintenanceService.update_maintenance(
            session, maintenance_id, **update_data
        )
    
    # ==================== 维护统计和分析 ====================
    
    @staticmethod
    def get_device_maintenance_history(
        session: Session,
        device_id: int,
        limit: int = 10
    ) -> List[DeviceMaintenance]:
        """
        获取设备的维护历史记录
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            limit: 返回记录数
            
        Returns:
            维护历史列表（按时间倒序）
        """
        return MaintenanceService.get_maintenance_list(
            session=session,
            device_id=device_id,
            limit=limit
        )
    
    @staticmethod
    def get_upcoming_maintenance(
        session: Session,
        days: int = 7
    ) -> List[DeviceMaintenance]:
        """
        获取即将到来的维护计划
        
        Args:
            session: 数据库会话
            days: 未来天数，默认7天
            
        Returns:
            即将进行的维护列表
        """
        now = datetime.now()
        future = now + timedelta(days=days)
        
        statement = (
            select(DeviceMaintenance)
            .where(
                and_(
                    DeviceMaintenance.status == MaintenanceStatus.SCHEDULED,
                    DeviceMaintenance.scheduled_time >= now,
                    DeviceMaintenance.scheduled_time <= future
                )
            )
            .order_by(DeviceMaintenance.scheduled_time)
        )
        
        return list(session.exec(statement).all())
    
    @staticmethod
    def get_overdue_maintenance(
        session: Session
    ) -> List[DeviceMaintenance]:
        """
        获取逾期未完成的维护计划
        
        Args:
            session: 数据库会话
            
        Returns:
            逾期维护列表
        """
        now = datetime.now()
        
        statement = (
            select(DeviceMaintenance)
            .where(
                and_(
                    DeviceMaintenance.status == MaintenanceStatus.SCHEDULED,
                    DeviceMaintenance.scheduled_time < now
                )
            )
            .order_by(DeviceMaintenance.scheduled_time)
        )
        
        return list(session.exec(statement).all())
    
    @staticmethod
    def get_maintenance_statistics(
        session: Session,
        device_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取维护统计信息
        
        Args:
            session: 数据库会话
            device_id: 设备ID（可选，不指定则统计所有设备）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            统计信息字典
        """
        # 构建基础查询
        statement = select(DeviceMaintenance)
        
        if device_id:
            statement = statement.where(DeviceMaintenance.device_id == device_id)
        
        if start_date:
            statement = statement.where(
                DeviceMaintenance.scheduled_time >= start_date
            )
        
        if end_date:
            statement = statement.where(
                DeviceMaintenance.scheduled_time <= end_date
            )
        
        records = list(session.exec(statement).all())
        
        # 统计各类数据
        total_count = len(records)
        
        # 按状态统计
        status_count = {}
        for status in MaintenanceStatus:
            status_count[status.value] = sum(
                1 for r in records if r.status == status.value
            )
        
        # 按类型统计
        type_count = {}
        for mtype in MaintenanceType:
            type_count[mtype.value] = sum(
                1 for r in records if r.maintenance_type == mtype.value
            )
        
        # 成本统计
        total_cost = sum(r.cost for r in records if r.cost)
        avg_cost = total_cost / total_count if total_count > 0 else 0
        
        # 时长统计
        completed_records = [
            r for r in records 
            if r.status == MaintenanceStatus.COMPLETED and r.duration_minutes
        ]
        total_duration = sum(r.duration_minutes for r in completed_records)
        avg_duration = (
            total_duration / len(completed_records) 
            if completed_records else 0
        )
        
        return {
            "total_count": total_count,
            "status_breakdown": status_count,
            "type_breakdown": type_count,
            "cost_statistics": {
                "total_cost": round(total_cost, 2),
                "average_cost": round(avg_cost, 2),
                "max_cost": max((r.cost for r in records if r.cost), default=0)
            },
            "duration_statistics": {
                "total_duration_minutes": total_duration,
                "average_duration_minutes": round(avg_duration, 2),
                "completed_count": len(completed_records)
            }
        }
    
    @staticmethod
    def delete_maintenance(session: Session, maintenance_id: int) -> None:
        """
        删除维护记录。记录不存在时抛出 ResourceNotFoundException，
        数据库错误由调用方/全局异常处理器处理。
        """
        maintenance = MaintenanceService.get_maintenance_by_id(
            session, maintenance_id
        )
        session.delete(maintenance)
        session.commit()
        logger.info(f"删除维护记录: id={maintenance_id}")
