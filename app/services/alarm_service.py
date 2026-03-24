"""
报警管理服务层
封装报警相关的业务逻辑
"""
import os
import json
from datetime import timedelta
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select
from datetime import datetime

from app.models.tables import Alarm
from app.core.logger import logger


ALARM_DEDUP_SECONDS = 300


class AlarmService:
    """
    报警管理服务类
    
    提供报警相关的业务逻辑，包括：
    - 获取未解决的报警列表
    - 批量解决报警
    - 报警统计和查询
    """
    
    @staticmethod
    def get_unresolved_alarms(session: Session, limit: int = 20) -> List[Alarm]:
        """
        获取未解决的报警列表
        
        Args:
            session: 数据库会话
            limit: 返回的最大记录数，默认20条
            
        Returns:
            未解决的报警列表，按时间倒序排列（最新的在前）
        """
        statement = (
            select(Alarm)
            .where(Alarm.is_resolved == False)
            .order_by(Alarm.timestamp.desc())
            .limit(limit)
        )
        alarms = session.exec(statement).all()
        return list(alarms)
    
    @staticmethod
    def resolve_all_alarms(session: Session) -> int:
        """
        批量解决所有未解决的报警
        
        Args:
            session: 数据库会话
            
        Returns:
            解决的报警数量
        """
        # 查询所有未解决的报警
        unresolved = session.exec(
            select(Alarm).where(Alarm.is_resolved == False)
        ).all()
        
        if not unresolved:
            return 0
        
        # 批量更新为已解决
        count = 0
        for alarm in unresolved:
            alarm.is_resolved = True
            session.add(alarm)
            count += 1
        
        # 提交事务
        session.commit()
        
        logger.info(f"批量解决了 {count} 条报警")
        return count
    
    @staticmethod
    def resolve_alarm(session: Session, alarm_id: int) -> bool:
        """
        解决单个报警
        
        Args:
            session: 数据库会话
            alarm_id: 报警ID
            
        Returns:
            是否成功解决，如果报警不存在或已解决则返回False
        """
        alarm = session.get(Alarm, alarm_id)
        if not alarm or alarm.is_resolved:
            return False
        
        alarm.is_resolved = True
        session.add(alarm)
        session.commit()
        
        logger.info(f"报警 {alarm_id} 已标记为已解决")
        return True
    
    @staticmethod
    def get_alarm_count(session: Session, device_id: int = None, resolved: bool = None) -> int:
        """
        获取报警数量统计
        
        Args:
            session: 数据库会话
            device_id: 设备ID，如果指定则只统计该设备的报警
            resolved: 是否已解决，None表示统计所有报警
            
        Returns:
            报警数量
        """
        statement = select(Alarm)
        
        if device_id is not None:
            statement = statement.where(Alarm.device_id == device_id)
        
        if resolved is not None:
            statement = statement.where(Alarm.is_resolved == resolved)
        
        alarms = session.exec(statement).all()
        return len(list(alarms))
    
    @staticmethod
    def create_alarm(
        session: Session,
        device_id: int,
        message: str,
        timestamp: datetime = None,
        auto_commit: bool = True,
    ) -> Alarm:
        """
        创建新的报警记录
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            message: 报警消息
            timestamp: 报警时间，如果为None则使用当前时间
            
        Returns:
            创建的报警对象
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        alarm = Alarm(
            device_id=device_id,
            message=message,
            timestamp=timestamp,
            is_resolved=False
        )
        
        session.add(alarm)
        if auto_commit:
            session.commit()
        else:
            session.flush()
        session.refresh(alarm)
        
        logger.info(f"创建报警: 设备 {device_id} - {message}")
        return alarm

    @staticmethod
    def should_create_alarm(
        session: Session,
        device_id: int,
        message: str,
        timestamp: datetime,
        dedup_seconds: int = ALARM_DEDUP_SECONDS,
    ) -> bool:
        """判断是否需要创建新报警，避免短时间内重复刷同类报警。"""
        if dedup_seconds <= 0:
            return True

        cutoff_time = timestamp - timedelta(seconds=dedup_seconds)
        existing_alarm = session.exec(
            select(Alarm)
            .where(Alarm.device_id == device_id)
            .where(Alarm.message == message)
            .where(Alarm.is_resolved == False)
            .where(Alarm.timestamp >= cutoff_time)
            .order_by(Alarm.timestamp.desc())
        ).first()

        return existing_alarm is None
    
    @staticmethod
    def load_thresholds() -> Dict:
        """
        加载报警阈值配置
        从 config/settings.json 读取
        """
        from app.core.settings import settings
        
        path = settings.settings_json_path or os.path.join(
            settings.config_dir, "settings.json"
        )
        
        try:
            if not os.path.exists(path):
                logger.warning(f"阈值配置文件不存在: {path}")
                return {}
            
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"阈值配置文件读取失败: {e}")
            return {}
    
    @staticmethod
    def check_and_create_alarm(
        session: Session,
        device_id: int,
        data: dict,
        timestamp: datetime
    ) -> list:
        """
        检查数据并创建报警
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            data: 数据字典
            timestamp: 时间戳
            
        Returns:
            创建的报警列表
        """
        alarms = []
        cfg = AlarmService.load_thresholds()
        defaults = cfg.get("default", {})
        dev_cfg = cfg.get("device_thresholds", {}).get(str(device_id), {})
        
        # 电流过载检测
        if "current" in data and data["current"] is not None:
            current = float(data["current"])
            limit = dev_cfg.get("current_max", defaults.get("current_max", 45.0))
            
            if current > limit:
                message = f"⚠️ 过载报警! 当前: {current}A (上限: {limit}A)"
                if AlarmService.should_create_alarm(session, device_id, message, timestamp):
                    alarm = AlarmService.create_alarm(
                        session=session,
                        device_id=device_id,
                        message=message,
                        timestamp=timestamp,
                        auto_commit=False,
                    )
                    alarms.append(alarm)
                    logger.warning(f"设备 {device_id} 电流过载: {current}A > {limit}A")
        
        # 电压异常检测
        if "voltage" in data and data["voltage"] is not None:
            voltage = float(data["voltage"])
            # 支持设备个性化电压配置，优先使用设备配置，否则使用默认值
            v_max = dev_cfg.get("voltage_max", defaults.get("voltage_max", 250.0))
            v_min = dev_cfg.get("voltage_min", defaults.get("voltage_min", 190.0))
            
            if voltage > v_max or voltage < v_min:
                message = f"⚡ 电压异常! 读数: {voltage}V (范围: {v_min}-{v_max}V)"
                if AlarmService.should_create_alarm(session, device_id, message, timestamp):
                    alarm = AlarmService.create_alarm(
                        session=session,
                        device_id=device_id,
                        message=message,
                        timestamp=timestamp,
                        auto_commit=False,
                    )
                    alarms.append(alarm)
                    logger.warning(f"设备 {device_id} 电压异常: {voltage}V")

        if alarms:
            session.commit()
            for alarm in alarms:
                session.refresh(alarm)
        
        return alarms
