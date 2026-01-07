"""
数据分析服务层
封装数据分析相关的业务逻辑
"""
from datetime import datetime, time
from typing import Dict, Any, Optional
from sqlmodel import Session, select

from app.models.tables import Device, DeviceData
from app.core.config import load_thresholds


class AnalysisService:
    """数据分析服务类"""
    
    @staticmethod
    def analyze_device(session: Session, device_id: int) -> Dict[str, Any]:
        """分析设备数据"""
        # 获取设备状态
        device = session.get(Device, device_id)
        is_active = device.is_active if device else False
        
        # 加载电价配置
        settings = load_thresholds()
        price_per_kwh = settings.get("default", {}).get("electricity_price", 0.85)
        
        # 获取最新数据
        latest = AnalysisService._get_latest_data(session, device_id)
        if not latest:
            return AnalysisService._empty_analysis(device_id, is_active)
        
        # 计算今日能耗
        today_kwh, today_cost = AnalysisService._calculate_today_consumption(
            session, device_id, latest, price_per_kwh
        )
        
        return {
            "device_id": device_id,
            "is_active": is_active,
            "current_power": round(latest.power, 2),
            "voltage": round(latest.voltage, 1),
            "current": round(latest.current, 2),
            "today_energy": round(today_kwh, 2),
            "today_cost": round(today_cost, 2),
        }
    
    @staticmethod
    def _get_latest_data(session: Session, device_id: int) -> Optional[DeviceData]:
        """获取设备最新数据"""
        return session.exec(
            select(DeviceData)
            .where(DeviceData.device_id == device_id)
            .order_by(DeviceData.timestamp.desc())
            .limit(1)
        ).first()
    
    @staticmethod
    def _calculate_today_consumption(
        session: Session,
        device_id: int,
        latest: DeviceData,
        price_per_kwh: float
    ) -> tuple[float, float]:
        """计算今日能耗和费用"""
        now = datetime.now()
        today_start = datetime.combine(now.date(), time.min)
        
        first_today = session.exec(
            select(DeviceData)
            .where(DeviceData.device_id == device_id)
            .where(DeviceData.timestamp >= today_start)
            .order_by(DeviceData.timestamp.asc())
            .limit(1)
        ).first()
        
        today_kwh = (latest.energy - first_today.energy) if first_today else 0
        today_cost = today_kwh * price_per_kwh
        
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

