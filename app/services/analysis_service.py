"""
数据分析服务层
封装数据分析相关的业务逻辑
"""
from datetime import datetime, time
from typing import Dict, Any, Optional
from sqlmodel import Session

from app.domain.device_payloads import describe_energy_data_fields, describe_device_type_semantics
from app.domain.energy_rules import calculate_energy_cost, get_energy_semantics
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
        energy_type = device.energy_type if device else "electricity"
        semantics = get_energy_semantics(energy_type)
        device_type_semantics = describe_device_type_semantics(device.device_type) if device else {}

        # 获取最新数据
        latest = AnalysisService._get_latest_data(session, device_id, energy_type)
        if not latest:
            return AnalysisService._empty_analysis(
                is_active,
                energy_type,
                semantics,
                device_type=device.device_type if device else None,
                device_category=device.device_category if device else None,
                device_type_semantics=device_type_semantics,
            )

        # 计算当日消耗与费用
        today_consumption, today_cost = AnalysisService._calculate_today_consumption(
            session, device_id, energy_type, latest
        )

        return {
            "is_active": is_active,
            "device_type": device.device_type if device else None,
            "device_category": device.device_category if device else None,
            "energy_type": energy_type,
            "semantics": semantics,
            "device_type_semantics": device_type_semantics,
            "energy_data_fields": describe_energy_data_fields(device.device_type) if device else {},
            "latest": latest,
            "today_consumption": today_consumption,
            "today_cost": today_cost,
        }

    @staticmethod
    def _get_latest_data(
        session: Session,
        device_id: int,
        energy_type: Optional[str] = None,
    ) -> Optional[EnergyData]:
        """获取设备最新数据"""
        return EnergyRepository.get_latest_energy_data(session, device_id, energy_type=energy_type)
    
    @staticmethod
    def _calculate_today_consumption(
        session: Session,
        device_id: int,
        energy_type: str,
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
            energy_type=energy_type,
        )
        
        today_value = (latest.consumption - first_today.consumption) if first_today else 0
        today_value = max(today_value, 0)
        today_cost = calculate_energy_cost(energy_type, today_value, now)

        return today_value, today_cost

    @staticmethod
    def _empty_analysis(
        is_active: bool,
        energy_type: str,
        semantics: Dict[str, Any],
        device_type: Optional[str] = None,
        device_category: Optional[str] = None,
        device_type_semantics: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """返回空数据分析结果"""
        return {
            "is_active": is_active,
            "device_type": device_type,
            "device_category": device_category,
            "energy_type": energy_type,
            "semantics": semantics,
            "device_type_semantics": device_type_semantics or {},
            "energy_data_fields": describe_energy_data_fields(device_type) if device_type else {},
            "latest": None,
            "today_consumption": 0,
            "today_cost": 0,
        }
