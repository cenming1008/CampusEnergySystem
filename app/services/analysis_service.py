"""
数据分析服务层
封装数据分析相关的业务逻辑
"""
from datetime import datetime, time
from typing import Dict, Any, Optional
from sqlmodel import Session, select

from app.models.tables import Device, EnergyData
from app.services.energy_service import EnergyService


class AnalysisService:
    """数据分析服务类"""

    @staticmethod
    def analyze_device(session: Session, device_id: int) -> Dict[str, Any]:
        """分析设备数据"""
        # 获取设备状态
        device = session.get(Device, device_id)
        is_active = device.is_active if device else False
        
        # 获取最新数据
        latest = AnalysisService._get_latest_data(session, device_id)
        if not latest:
            return AnalysisService._empty_analysis(device_id, is_active)
        
        # 计算今日能耗（使用峰谷平电价）
        today_kwh, today_cost = AnalysisService._calculate_today_consumption(
            session, device_id, latest
        )
        
        return {
            "device_id": device_id,
            "is_active": is_active,
            "current_power": round(latest.flow_rate or 0, 2),
            "voltage": round(latest.voltage or 0, 1),
            "current": round(latest.current or 0, 2),
            "today_energy": round(today_kwh, 2),
            "today_cost": round(today_cost, 2),
        }
    
    @staticmethod
    def _get_latest_data(session: Session, device_id: int) -> Optional[EnergyData]:
        """获取设备最新数据"""
        return session.exec(
            select(EnergyData)
            .where(EnergyData.device_id == device_id)
            .order_by(EnergyData.timestamp.desc())
            .limit(1)
        ).first()
    
    @staticmethod
    def _calculate_today_consumption(
        session: Session,
        device_id: int,
        latest: EnergyData
    ) -> tuple[float, float]:
        """
        计算今日能耗和费用（使用峰谷平电价）
        
        注意：这里简化处理，使用当前时段的电价估算总费用。
        更精确的方法是逐小时计算，但会增加复杂度。
        """
        now = datetime.now()
        today_start = datetime.combine(now.date(), time.min)
        
        first_today = session.exec(
            select(EnergyData)
            .where(EnergyData.device_id == device_id)
            .where(EnergyData.timestamp >= today_start)
            .order_by(EnergyData.timestamp.asc())
            .limit(1)
        ).first()
        
        today_kwh = (latest.consumption - first_today.consumption) if first_today else 0
        
        # 使用当前时段的电价（简化计算）
        # 更精确的方法：可以按小时查询能耗，分时段计算费用
        current_price = EnergyService.get_electricity_price(now.hour)
        today_cost = today_kwh * current_price
        
        return today_kwh, today_cost
    
    @staticmethod
    def _empty_analysis(device_id: int, is_active: bool) -> Dict[str, Any]:
        """返回空数据分析结果"""
        return {
            "device_id": device_id,
            "is_active": is_active,
            "current_power": 0,
            "today_energy": 0,
            "today_cost": 0,
            "voltage": 0,
            "current": 0
        }

