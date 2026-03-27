"""
数据分析服务层
封装数据分析相关的业务逻辑
"""
from datetime import datetime, time
from typing import Dict, Any, Optional
from sqlmodel import Session

from app.domain.energy_rules import get_electricity_price
from app.models.tables import EnergyData
from app.repositories.device_repository import DeviceRepository
from app.repositories.energy_repository import EnergyRepository


class AnalysisService:
    """数据分析服务类"""

    @staticmethod
    def analyze_device(session: Session, device_id: int) -> Dict[str, Any]:
        """分析设备数据"""
        # 获取设备状态
        device = DeviceRepository.get_by_id(session, device_id)
        is_active = device.is_active if device else False
        
        # 获取最新数据
        latest = AnalysisService._get_latest_data(session, device_id)
        if not latest:
            return AnalysisService._empty_analysis(is_active)
        
        # 计算今日能耗（使用峰谷平电价）
        today_kwh, today_cost = AnalysisService._calculate_today_consumption(
            session, device_id, latest
        )
        
        return {
            "is_active": is_active,
            "latest": latest,
            "today_energy": today_kwh,
            "today_cost": today_cost,
        }
    
    @staticmethod
    def _get_latest_data(session: Session, device_id: int) -> Optional[EnergyData]:
        """获取设备最新数据"""
        return EnergyRepository.get_latest_energy_data(session, device_id)
    
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
        
        first_today = EnergyRepository.get_first_energy_data_since(
            session=session,
            device_id=device_id,
            start_time=today_start,
        )
        
        today_kwh = (latest.consumption - first_today.consumption) if first_today else 0
        
        # 使用当前时段的电价（简化计算）
        # 更精确的方法：可以按小时查询能耗，分时段计算费用
        current_price = get_electricity_price(now.hour)
        today_cost = today_kwh * current_price
        
        return today_kwh, today_cost
    
    @staticmethod
    def _empty_analysis(is_active: bool) -> Dict[str, Any]:
        """返回空数据分析结果"""
        return {
            "is_active": is_active,
            "latest": None,
            "today_energy": 0,
            "today_cost": 0,
        }
