"""
巡检运维服务层
封装巡检相关的业务逻辑
"""
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timedelta
from sqlmodel import Session, select, func, and_
from app.core.logger import logger
import json
import uuid

from app.models.tables import (
    InspectionRoute, InspectionPoint, InspectionPlan,
    InspectionTask, InspectionRecord, Device,
    InspectionStatus, InspectionResult
)
from app.core.exceptions import ResourceNotFoundException, DatabaseException, ConflictException


class InspectionService:
    """
    巡检运维服务类
    
    提供巡检相关的业务逻辑，包括：
    - 巡检路线管理
    - 巡检点管理
    - 巡检计划管理
    - 巡检任务执行
    - 巡检记录和统计
    """
    
    # ==================== 巡检路线管理 ====================
    
    @staticmethod
    def create_route(
        session: Session,
        name: str,
        code: Optional[str] = None,
        description: Optional[str] = None,
        estimated_duration: int = 30
    ) -> InspectionRoute:
        """创建巡检路线"""
        route = InspectionRoute(
            name=name,
            code=code,
            description=description,
            estimated_duration=estimated_duration
        )
        
        session.add(route)
        session.commit()
        session.refresh(route)
        
        logger.info(f"创建巡检路线: {name} (ID={route.id})")
        return route
    
    @staticmethod
    def get_route_by_id(session: Session, route_id: int) -> InspectionRoute:
        """根据ID获取巡检路线"""
        route = session.get(InspectionRoute, route_id)
        if not route:
            raise ResourceNotFoundException("巡检路线", route_id)
        return route
    
    @staticmethod
    def get_all_routes(
        session: Session,
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 50
    ) -> List[InspectionRoute]:
        """获取所有巡检路线（支持分页）"""
        statement = select(InspectionRoute)
        if is_active is not None:
            statement = statement.where(InspectionRoute.is_active == is_active)
        statement = statement.order_by(InspectionRoute.id).offset(offset).limit(limit)
        return list(session.exec(statement).all())
    
    @staticmethod
    def update_route(
        session: Session,
        route_id: int,
        **update_fields
    ) -> InspectionRoute:
        """更新巡检路线"""
        route = InspectionService.get_route_by_id(session, route_id)
        
        for field, value in update_fields.items():
            if hasattr(route, field) and value is not None:
                setattr(route, field, value)
        
        route.updated_at = datetime.now()
        session.add(route)
        session.commit()
        session.refresh(route)
        
        return route
    
    @staticmethod
    def delete_route(session: Session, route_id: int, force: bool = False) -> bool:
        """
        删除巡检路线
        
        Args:
            session: 数据库会话
            route_id: 路线ID
            force: 是否强制删除（同时删除关联的巡检点、计划、任务）
        """
        route = InspectionService.get_route_by_id(session, route_id)
        
        # 检查关联数据
        points_count = session.exec(
            select(func.count()).where(InspectionPoint.route_id == route_id)
        ).one()
        plans_count = session.exec(
            select(func.count()).where(InspectionPlan.route_id == route_id)
        ).one()
        tasks_count = session.exec(
            select(func.count()).where(InspectionTask.route_id == route_id)
        ).one()
        
        if not force and (points_count > 0 or plans_count > 0 or tasks_count > 0):
            raise ConflictException(
                f"无法删除路线：存在 {points_count} 个巡检点、{plans_count} 个计划、{tasks_count} 个任务。"
                f"如需强制删除，请使用 force=True 参数。"
            )
        
        # 强制删除时，先删除关联数据
        if force:
            # 删除巡检记录（通过任务）
            tasks = session.exec(
                select(InspectionTask).where(InspectionTask.route_id == route_id)
            ).all()
            for task in tasks:
                records = session.exec(
                    select(InspectionRecord).where(InspectionRecord.task_id == task.id)
                ).all()
                for record in records:
                    session.delete(record)
            
            # 删除任务
            for task in tasks:
                session.delete(task)
            
            # 删除计划
            plans = session.exec(
                select(InspectionPlan).where(InspectionPlan.route_id == route_id)
            ).all()
            for plan in plans:
                session.delete(plan)
            
            # 删除巡检点
            points = session.exec(
                select(InspectionPoint).where(InspectionPoint.route_id == route_id)
            ).all()
            for point in points:
                session.delete(point)
        
        session.delete(route)
        session.commit()
        logger.info(f"删除巡检路线: ID={route_id}, force={force}")
        return True
    
    # ==================== 巡检点管理 ====================
    
    @staticmethod
    def add_point_to_route(
        session: Session,
        route_id: int,
        name: str,
        device_id: Optional[int] = None,
        location: Optional[str] = None,
        sequence: int = 0,
        check_items: Optional[List[str]] = None,
        qr_code: Optional[str] = None,
        is_required: bool = True
    ) -> InspectionPoint:
        """添加巡检点到路线"""
        # 验证路线存在
        route = InspectionService.get_route_by_id(session, route_id)
        
        # 验证设备存在（如果提供）
        if device_id:
            device = session.get(Device, device_id)
            if not device:
                raise ResourceNotFoundException("设备", device_id)
        
        # 默认检查项目
        if check_items is None:
            check_items = ["外观检查", "运行状态", "仪表读数", "异常声音", "温度检查"]
        
        point = InspectionPoint(
            route_id=route_id,
            device_id=device_id,
            name=name,
            location=location,
            sequence=sequence,
            check_items=json.dumps(check_items, ensure_ascii=False),
            qr_code=qr_code,
            is_required=is_required
        )
        
        session.add(point)
        
        # 更新路线的设备数量
        route.device_count += 1
        session.add(route)
        
        session.commit()
        session.refresh(point)
        
        logger.info(f"添加巡检点: {name} -> 路线 {route.name}")
        return point
    
    @staticmethod
    def get_route_points(
        session: Session,
        route_id: int
    ) -> List[InspectionPoint]:
        """获取路线的所有巡检点（按顺序）"""
        statement = (
            select(InspectionPoint)
            .where(InspectionPoint.route_id == route_id)
            .where(InspectionPoint.is_active == True)
            .order_by(InspectionPoint.sequence)
        )
        return list(session.exec(statement).all())
    
    @staticmethod
    def update_point(
        session: Session,
        point_id: int,
        **update_fields
    ) -> InspectionPoint:
        """更新巡检点"""
        point = session.get(InspectionPoint, point_id)
        if not point:
            raise ResourceNotFoundException("巡检点", point_id)
        
        # 处理 check_items（如果是列表，转为JSON）
        if 'check_items' in update_fields:
            items = update_fields['check_items']
            if isinstance(items, list):
                update_fields['check_items'] = json.dumps(items, ensure_ascii=False)
        
        for field, value in update_fields.items():
            if hasattr(point, field) and value is not None:
                setattr(point, field, value)
        
        session.add(point)
        session.commit()
        session.refresh(point)
        
        return point
    
    @staticmethod
    def delete_point(session: Session, point_id: int) -> bool:
        """删除巡检点"""
        point = session.get(InspectionPoint, point_id)
        if not point:
            raise ResourceNotFoundException("巡检点", point_id)
        
        route_id = point.route_id
        session.delete(point)
        
        # 更新路线的设备数量
        route = session.get(InspectionRoute, route_id)
        if route and route.device_count > 0:
            route.device_count -= 1
            session.add(route)
        
        session.commit()
        return True
    
    # ==================== 巡检计划管理 ====================
    
    @staticmethod
    def create_plan(
        session: Session,
        route_id: int,
        name: str,
        plan_type: str = "daily",
        start_date: datetime = None,
        end_date: Optional[datetime] = None,
        execution_time: str = "08:00",
        assigned_to: Optional[str] = None,
        department: Optional[str] = None,
        schedule_config: Optional[Dict] = None
    ) -> InspectionPlan:
        """创建巡检计划"""
        # 验证路线存在
        route = InspectionService.get_route_by_id(session, route_id)
        
        if start_date is None:
            start_date = datetime.now()
        
        plan = InspectionPlan(
            route_id=route_id,
            name=name,
            plan_type=plan_type,
            start_date=start_date,
            end_date=end_date,
            execution_time=execution_time,
            assigned_to=assigned_to,
            department=department,
            schedule_config=json.dumps(schedule_config) if schedule_config else None
        )
        
        session.add(plan)
        session.commit()
        session.refresh(plan)
        
        logger.info(f"创建巡检计划: {name} (类型={plan_type})")
        return plan
    
    @staticmethod
    def get_all_plans(
        session: Session,
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 50
    ) -> List[InspectionPlan]:
        """获取所有巡检计划（支持分页）"""
        statement = select(InspectionPlan)
        if is_active is not None:
            statement = statement.where(InspectionPlan.is_active == is_active)
        statement = statement.order_by(InspectionPlan.start_date.desc()).offset(offset).limit(limit)
        return list(session.exec(statement).all())
    
    @staticmethod
    def get_plan_by_id(session: Session, plan_id: int) -> InspectionPlan:
        """根据ID获取巡检计划"""
        plan = session.get(InspectionPlan, plan_id)
        if not plan:
            raise ResourceNotFoundException("巡检计划", plan_id)
        return plan
    
    @staticmethod
    def update_plan(
        session: Session,
        plan_id: int,
        **update_fields
    ) -> InspectionPlan:
        """更新巡检计划"""
        plan = InspectionService.get_plan_by_id(session, plan_id)
        
        # 如果更新路线，需要验证路线存在
        if 'route_id' in update_fields and update_fields['route_id'] is not None:
            InspectionService.get_route_by_id(session, update_fields['route_id'])
        
        # 处理 schedule_config（如果是字典，转为JSON）
        if 'schedule_config' in update_fields:
            config = update_fields['schedule_config']
            if isinstance(config, dict):
                update_fields['schedule_config'] = json.dumps(config)
        
        for field, value in update_fields.items():
            if hasattr(plan, field) and value is not None:
                setattr(plan, field, value)
        
        session.add(plan)
        session.commit()
        session.refresh(plan)
        
        logger.info(f"更新巡检计划: ID={plan_id}")
        return plan
    
    @staticmethod
    def delete_plan(session: Session, plan_id: int, force: bool = False) -> bool:
        """
        删除巡检计划
        
        Args:
            session: 数据库会话
            plan_id: 计划ID
            force: 是否强制删除（同时删除关联的任务）
        """
        plan = InspectionService.get_plan_by_id(session, plan_id)
        
        # 检查是否有关联任务
        tasks_count = session.exec(
            select(func.count()).where(InspectionTask.plan_id == plan_id)
        ).one()
        
        if not force and tasks_count > 0:
            raise ConflictException(
                f"无法删除计划：存在 {tasks_count} 个关联任务。"
                f"如需强制删除，请使用 force=True 参数。"
            )
        
        # 强制删除时，取消关联任务的计划关联（而不是删除任务）
        if force and tasks_count > 0:
            tasks = session.exec(
                select(InspectionTask).where(InspectionTask.plan_id == plan_id)
            ).all()
            for task in tasks:
                task.plan_id = None
                session.add(task)
        
        session.delete(plan)
        session.commit()
        logger.info(f"删除巡检计划: ID={plan_id}, force={force}")
        return True
    
    # ==================== 巡检任务管理 ====================
    
    @staticmethod
    def generate_task_no() -> str:
        """生成任务编号（时间戳 + 随机后缀，避免重复）"""
        now = datetime.now()
        # 添加 4 位随机后缀防止同一秒内重复
        suffix = uuid.uuid4().hex[:4].upper()
        return f"XJ{now.strftime('%Y%m%d%H%M%S')}{suffix}"
    
    @staticmethod
    def create_task(
        session: Session,
        route_id: int,
        task_date: datetime = None,
        plan_id: Optional[int] = None,
        inspector: Optional[str] = None
    ) -> InspectionTask:
        """创建巡检任务"""
        route = InspectionService.get_route_by_id(session, route_id)
        
        if task_date is None:
            task_date = datetime.now()
        
        # 获取巡检点数量
        points = InspectionService.get_route_points(session, route_id)
        total_points = len(points)
        
        task = InspectionTask(
            plan_id=plan_id,
            route_id=route_id,
            task_no=InspectionService.generate_task_no(),
            task_date=task_date,
            status=InspectionStatus.PENDING,
            inspector=inspector,
            total_points=total_points
        )
        
        session.add(task)
        session.commit()
        session.refresh(task)
        
        logger.info(f"创建巡检任务: {task.task_no} (路线={route.name})")
        return task
    
    @staticmethod
    def get_task_by_id(session: Session, task_id: int) -> InspectionTask:
        """根据ID获取巡检任务"""
        task = session.get(InspectionTask, task_id)
        if not task:
            raise ResourceNotFoundException("巡检任务", task_id)
        return task
    
    @staticmethod
    def get_tasks(
        session: Session,
        status: Optional[str] = None,
        inspector: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        allowed_route_ids: Optional[Set[int]] = None,
        limit: int = 50
    ) -> List[InspectionTask]:
        """获取巡检任务列表"""
        statement = select(InspectionTask)

        if allowed_route_ids is not None:
            if not allowed_route_ids:
                return []
            statement = statement.where(InspectionTask.route_id.in_(allowed_route_ids))
        
        if status:
            statement = statement.where(InspectionTask.status == status)
        if inspector:
            statement = statement.where(InspectionTask.inspector == inspector)
        if start_date:
            statement = statement.where(InspectionTask.task_date >= start_date)
        if end_date:
            statement = statement.where(InspectionTask.task_date <= end_date)
        
        statement = statement.order_by(InspectionTask.task_date.desc()).limit(limit)
        return list(session.exec(statement).all())
    
    @staticmethod
    def start_task(
        session: Session,
        task_id: int,
        inspector: Optional[str] = None
    ) -> InspectionTask:
        """开始执行巡检任务"""
        task = InspectionService.get_task_by_id(session, task_id)
        
        # 状态校验：只有待执行或已逾期的任务可以开始
        if task.status not in [InspectionStatus.PENDING, InspectionStatus.OVERDUE]:
            raise ConflictException(
                f"无法开始任务：当前状态为 {task.status}，只有待执行或已逾期的任务可以开始"
            )
        
        task.status = InspectionStatus.IN_PROGRESS
        task.start_time = datetime.now()
        
        if inspector:
            task.inspector = inspector
        
        task.updated_at = datetime.now()
        session.add(task)
        session.commit()
        session.refresh(task)
        
        logger.info(f"开始巡检任务: {task.task_no}")
        return task
    
    @staticmethod
    def complete_task(
        session: Session,
        task_id: int,
        remark: Optional[str] = None
    ) -> InspectionTask:
        """完成巡检任务"""
        task = InspectionService.get_task_by_id(session, task_id)
        
        # 状态校验：只有进行中的任务可以完成
        if task.status != InspectionStatus.IN_PROGRESS:
            raise ConflictException(
                f"无法完成任务：当前状态为 {task.status}，只有进行中的任务可以完成"
            )
        
        task.status = InspectionStatus.COMPLETED
        task.end_time = datetime.now()
        
        # 计算耗时
        if task.start_time:
            duration = task.end_time - task.start_time
            task.duration_minutes = int(duration.total_seconds() / 60)
        
        if remark:
            task.remark = remark
        
        task.updated_at = datetime.now()
        session.add(task)
        session.commit()
        session.refresh(task)
        
        logger.info(f"完成巡检任务: {task.task_no}")
        return task
    
    # ==================== 巡检记录管理 ====================
    
    @staticmethod
    def submit_inspection_record(
        session: Session,
        task_id: int,
        point_id: int,
        result: str = InspectionResult.NORMAL,
        check_details: Optional[Dict] = None,
        meter_reading: Optional[float] = None,
        abnormal_description: Optional[str] = None,
        abnormal_level: Optional[str] = None,
        images: Optional[List[str]] = None,
        inspector: Optional[str] = None
    ) -> InspectionRecord:
        """提交巡检点检查记录"""
        task = InspectionService.get_task_by_id(session, task_id)
        point = session.get(InspectionPoint, point_id)
        if not point:
            raise ResourceNotFoundException("巡检点", point_id)
        
        # 检查任务状态：只有进行中的任务可以提交记录
        if task.status != InspectionStatus.IN_PROGRESS:
            raise ConflictException(
                f"无法提交记录：任务状态为 {task.status}，只有进行中的任务可以提交记录"
            )
        
        # 检查是否已经提交过该巡检点的记录
        existing_record = session.exec(
            select(InspectionRecord).where(
                and_(
                    InspectionRecord.task_id == task_id,
                    InspectionRecord.point_id == point_id
                )
            )
        ).first()
        
        if existing_record:
            raise ConflictException(
                f"该巡检点已提交过记录（记录ID: {existing_record.id}），请勿重复提交"
            )
        
        record = InspectionRecord(
            task_id=task_id,
            point_id=point_id,
            device_id=point.device_id,
            result=result,
            check_time=datetime.now(),
            check_details=json.dumps(check_details, ensure_ascii=False) if check_details else None,
            meter_reading=meter_reading,
            abnormal_description=abnormal_description,
            abnormal_level=abnormal_level,
            images=json.dumps(images) if images else None,
            inspector=inspector or task.inspector
        )
        
        session.add(record)
        
        # 更新任务统计
        task.completed_points += 1
        if result in [InspectionResult.ABNORMAL, InspectionResult.DEFECT, InspectionResult.SERIOUS]:
            task.abnormal_count += 1
        
        task.updated_at = datetime.now()
        session.add(task)
        
        session.commit()
        session.refresh(record)
        
        logger.info(f"提交巡检记录: 任务={task.task_no}, 巡检点={point.name}, 结果={result}")
        return record
    
    @staticmethod
    def get_task_records(
        session: Session,
        task_id: int
    ) -> List[InspectionRecord]:
        """获取任务的所有巡检记录"""
        statement = (
            select(InspectionRecord)
            .where(InspectionRecord.task_id == task_id)
            .order_by(InspectionRecord.check_time)
        )
        return list(session.exec(statement).all())
    
    # ==================== 统计分析 ====================
    
    @staticmethod
    def get_inspection_statistics(
        session: Session,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        allowed_route_ids: Optional[Set[int]] = None,
    ) -> Dict[str, Any]:
        """获取巡检统计信息"""
        # 默认统计最近30天
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # 查询任务
        statement = (
            select(InspectionTask)
            .where(InspectionTask.task_date >= start_date)
            .where(InspectionTask.task_date <= end_date)
        )
        if allowed_route_ids is not None:
            if not allowed_route_ids:
                tasks = []
            else:
                statement = statement.where(InspectionTask.route_id.in_(allowed_route_ids))
        tasks = list(session.exec(statement).all()) if allowed_route_ids != set() else []
        
        # 统计
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.status == InspectionStatus.COMPLETED)
        pending_tasks = sum(1 for t in tasks if t.status == InspectionStatus.PENDING)
        overdue_tasks = sum(1 for t in tasks if t.status == InspectionStatus.OVERDUE)
        
        total_points = sum(t.total_points for t in tasks)
        completed_points = sum(t.completed_points for t in tasks)
        abnormal_count = sum(t.abnormal_count for t in tasks)
        
        # 计算完成率
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        point_completion_rate = (completed_points / total_points * 100) if total_points > 0 else 0
        abnormal_rate = (abnormal_count / completed_points * 100) if completed_points > 0 else 0
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "tasks": {
                "total": total_tasks,
                "completed": completed_tasks,
                "pending": pending_tasks,
                "overdue": overdue_tasks,
                "completion_rate": round(completion_rate, 1)
            },
            "points": {
                "total": total_points,
                "completed": completed_points,
                "completion_rate": round(point_completion_rate, 1)
            },
            "abnormal": {
                "count": abnormal_count,
                "rate": round(abnormal_rate, 1)
            }
        }
    
    @staticmethod
    def get_today_tasks(
        session: Session,
        allowed_route_ids: Optional[Set[int]] = None,
    ) -> List[InspectionTask]:
        """获取今日巡检任务"""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        statement = (
            select(InspectionTask)
            .where(InspectionTask.task_date >= datetime.combine(today, datetime.min.time()))
            .where(InspectionTask.task_date < datetime.combine(tomorrow, datetime.min.time()))
            .order_by(InspectionTask.task_date)
        )
        if allowed_route_ids is not None:
            if not allowed_route_ids:
                return []
            statement = statement.where(InspectionTask.route_id.in_(allowed_route_ids))
        return list(session.exec(statement).all())
    
    @staticmethod
    def get_pending_tasks(
        session: Session,
        limit: int = 10,
        allowed_route_ids: Optional[Set[int]] = None,
    ) -> List[InspectionTask]:
        """获取待执行的巡检任务"""
        statement = (
            select(InspectionTask)
            .where(InspectionTask.status == InspectionStatus.PENDING)
            .order_by(InspectionTask.task_date)
            .limit(limit)
        )
        if allowed_route_ids is not None:
            if not allowed_route_ids:
                return []
            statement = statement.where(InspectionTask.route_id.in_(allowed_route_ids))
        return list(session.exec(statement).all())
