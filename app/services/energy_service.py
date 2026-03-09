"""
能源数据服务 - 处理多种能源类型的数据采集和分析
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from sqlmodel import Session, select, func
from app.core.logger import logger

from app.models.tables import (
    Device, EnergyData, CarbonEmission, EnergyStatistics,
    EnergyType
)
from app.core.settings import settings


def _parse_hour_ranges(ranges_str: str) -> List[Tuple[int, int]]:
    """
    解析时段配置字符串为 (start, end) 列表，左闭右开。
    例如 "8-12,18-23" -> [(8, 12), (18, 23)]
    """
    result = []
    for part in ranges_str.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            a, b = part.split("-", 1)
            start, end = int(a.strip()), int(b.strip())
            if 0 <= start <= 24 and 0 <= end <= 24 and start < end:
                result.append((start, end))
        except (ValueError, AttributeError):
            continue
    return result


def _is_hour_in_ranges(hour: int, ranges: List[Tuple[int, int]]) -> bool:
    """判断 hour (0-23) 是否落在任意区间 [start, end) 内。"""
    for start, end in ranges:
        if start <= hour < end:
            return True
    return False


class EnergyService:
    """能源数据服务类"""
    
    # 碳排放因子 (kg CO2 / 单位)
    CARBON_FACTORS = {
        EnergyType.ELECTRICITY: 0.5839,  # kg CO2/kWh (国家电网平均)
        EnergyType.GAS: 2.162,           # kg CO2/m³ (天然气)
        EnergyType.HEAT: 0.11,           # kg CO2/kWh (集中供热)
        EnergyType.WATER: 0.167,         # kg CO2/m³ (自来水)
        EnergyType.COOLING: 0.13,        # kg CO2/kWh (制冷)
        EnergyType.STEAM: 0.12,          # kg CO2/kg (蒸汽)
    }
    
    # 能源单位映射
    ENERGY_UNITS = {
        EnergyType.ELECTRICITY: "kWh",
        EnergyType.WATER: "m³",
        EnergyType.GAS: "m³",
        EnergyType.HEAT: "GJ",
        EnergyType.COOLING: "kWh",
        EnergyType.STEAM: "t",
    }
    
    # 能源价格（元/单位）- 可根据实际情况调整
    ENERGY_PRICES = {
        EnergyType.WATER: 3.5,      # 元/m³
        EnergyType.GAS: 2.8,        # 元/m³
        EnergyType.HEAT: 25.0,      # 元/GJ
        EnergyType.COOLING: 0.6,    # 元/kWh
        EnergyType.STEAM: 180.0,    # 元/t
        # 注意：电力使用峰谷平电价，不在此处定义
    }
    
    @staticmethod
    def get_electricity_price(hour: int) -> float:
        """
        根据时段获取电价（峰谷平电价），时段由配置决定。
        
        默认：峰 8-12,18-23；平 7-8,12-18；其余为谷。
        可通过 settings.electricity_peak_hours / electricity_flat_hours 配置。
        
        Args:
            hour: 小时数 (0-23)
        
        Returns:
            电价（元/kWh）
        """
        hour = max(0, min(23, int(hour)))
        peak_ranges = _parse_hour_ranges(settings.electricity_peak_hours)
        flat_ranges = _parse_hour_ranges(settings.electricity_flat_hours)
        if _is_hour_in_ranges(hour, peak_ranges):
            return settings.peak_price
        if _is_hour_in_ranges(hour, flat_ranges):
            return settings.flat_price
        return settings.valley_price
    
    @staticmethod
    def calculate_energy_cost(
        energy_type: str,
        consumption: float,
        timestamp: datetime
    ) -> float:
        """
        计算能源成本
        
        Args:
            energy_type: 能源类型
            consumption: 消耗量
            timestamp: 时间戳
        
        Returns:
            成本（元）
        """
        if energy_type == EnergyType.ELECTRICITY:
            # 电力使用峰谷平电价
            price = EnergyService.get_electricity_price(timestamp.hour)
        else:
            # 其他能源使用固定价格
            price = EnergyService.ENERGY_PRICES.get(energy_type, 0)
        
        return consumption * price
    
    @staticmethod
    def save_energy_data(
        session: Session,
        device_id: int,
        energy_type: str,
        consumption: float,
        flow_rate: Optional[float] = None,
        timestamp: Optional[datetime] = None,
        **kwargs
    ) -> EnergyData:
        """
        保存能源数据
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            energy_type: 能源类型
            consumption: 消耗量
            flow_rate: 瞬时流量/功率
            timestamp: 时间戳
            **kwargs: 其他可选字段
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # 验证设备存在且类型匹配
        device = session.get(Device, device_id)
        if not device:
            raise ValueError(f"设备 {device_id} 不存在")
        
        if device.energy_type != energy_type:
            logger.warning(
                f"设备 {device_id} 能源类型不匹配: "
                f"期望 {device.energy_type}, 实际 {energy_type}"
            )
        
        # 创建能源数据记录
        energy_data = EnergyData(
            device_id=device_id,
            timestamp=timestamp,
            energy_type=energy_type,
            consumption=consumption,
            flow_rate=flow_rate,
            **kwargs
        )
        
        session.add(energy_data)
        session.commit()
        session.refresh(energy_data)
        
        # 自动计算并保存碳排放
        EnergyService.calculate_carbon_emission(
            session, device_id, energy_type, consumption, timestamp
        )
        
        logger.info(
            f"保存能源数据: 设备={device_id}, 类型={energy_type}, "
            f"消耗={consumption}, 时间={timestamp}"
        )
        
        return energy_data
    
    @staticmethod
    def calculate_carbon_emission(
        session: Session,
        device_id: int,
        energy_type: str,
        consumption: float,
        timestamp: datetime
    ) -> CarbonEmission:
        """
        计算并保存碳排放数据
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            energy_type: 能源类型
            consumption: 能源消耗量
            timestamp: 时间戳
        """
        carbon_factor = EnergyService.CARBON_FACTORS.get(energy_type, 0)
        carbon_emission_value = consumption * carbon_factor
        
        unit = EnergyService.ENERGY_UNITS.get(energy_type, "")
        
        carbon_record = CarbonEmission(
            device_id=device_id,
            timestamp=timestamp,
            energy_type=energy_type,
            energy_consumption=consumption,
            consumption_unit=unit,
            carbon_factor=carbon_factor,
            carbon_emission=carbon_emission_value,
            scope=1 if energy_type in [EnergyType.GAS, EnergyType.HEAT] else 2
        )
        
        session.add(carbon_record)
        session.commit()
        session.refresh(carbon_record)
        
        logger.info(
            f"计算碳排放: 设备={device_id}, 排放={carbon_emission_value:.2f} kg CO2"
        )
        
        return carbon_record
    
    @staticmethod
    def get_energy_data(
        session: Session,
        device_id: int,
        energy_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[EnergyData]:
        """
        查询能源数据
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            energy_type: 能源类型（可选）
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回条数限制
        """
        statement = select(EnergyData).where(EnergyData.device_id == device_id)
        
        if energy_type:
            statement = statement.where(EnergyData.energy_type == energy_type)
        
        if start_time:
            statement = statement.where(EnergyData.timestamp >= start_time)
        
        if end_time:
            statement = statement.where(EnergyData.timestamp <= end_time)
        
        statement = statement.order_by(EnergyData.timestamp.desc()).limit(limit)
        
        results = session.exec(statement).all()
        return list(reversed(results))
    
    @staticmethod
    def get_carbon_emissions(
        session: Session,
        device_id: Optional[int] = None,
        energy_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[CarbonEmission]:
        """
        查询碳排放数据
        
        Args:
            session: 数据库会话
            device_id: 设备ID（可选，None表示所有设备）
            energy_type: 能源类型（可选）
            start_time: 开始时间
            end_time: 结束时间
        """
        statement = select(CarbonEmission)
        
        if device_id:
            statement = statement.where(CarbonEmission.device_id == device_id)
        
        if energy_type:
            statement = statement.where(CarbonEmission.energy_type == energy_type)
        
        if start_time:
            statement = statement.where(CarbonEmission.timestamp >= start_time)
        
        if end_time:
            statement = statement.where(CarbonEmission.timestamp <= end_time)
        
        statement = statement.order_by(CarbonEmission.timestamp.desc())
        
        return session.exec(statement).all()
    
    @staticmethod
    def calculate_statistics(
        session: Session,
        device_id: Optional[int],
        energy_type: str,
        start_time: datetime,
        end_time: datetime,
        period_type: str = "day"
    ) -> Dict:
        """
        计算能源统计数据
        
        Args:
            session: 数据库会话
            device_id: 设备ID（None表示系统级）
            energy_type: 能源类型
            start_time: 开始时间
            end_time: 结束时间
            period_type: 统计周期
        
        Returns:
            统计结果字典
        """
        statement = select(EnergyData).where(
            EnergyData.energy_type == energy_type,
            EnergyData.timestamp >= start_time,
            EnergyData.timestamp <= end_time
        )
        
        if device_id:
            statement = statement.where(EnergyData.device_id == device_id)
        
        results = session.exec(statement).all()
        
        if not results:
            return {
                "total_consumption": 0,
                "avg_consumption": 0,
                "avg_flow_rate": 0,
                "peak_flow_rate": 0,
                "data_count": 0
            }
        
        consumptions = [r.consumption for r in results]
        flow_rates = [r.flow_rate for r in results if r.flow_rate is not None]
        
        return {
            "total_consumption": sum(consumptions),
            "avg_consumption": sum(consumptions) / len(consumptions),
            "avg_flow_rate": sum(flow_rates) / len(flow_rates) if flow_rates else 0,
            "peak_flow_rate": max(flow_rates) if flow_rates else 0,
            "data_count": len(results)
        }
    
    @staticmethod
    def get_carbon_summary(
        session: Session,
        start_time: datetime,
        end_time: datetime,
        device_id: Optional[int] = None
    ) -> Dict:
        """
        获取碳排放汇总
        
        Args:
            session: 数据库会话
            start_time: 开始时间
            end_time: 结束时间
            device_id: 设备ID（可选）
        
        Returns:
            碳排放汇总字典
        """
        statement = select(
            CarbonEmission.energy_type,
            func.sum(CarbonEmission.carbon_emission).label("total_emission"),
            func.sum(CarbonEmission.energy_consumption).label("total_consumption")
        ).where(
            CarbonEmission.timestamp >= start_time,
            CarbonEmission.timestamp <= end_time
        )
        
        if device_id:
            statement = statement.where(CarbonEmission.device_id == device_id)
        
        statement = statement.group_by(CarbonEmission.energy_type)
        
        results = session.exec(statement).all()
        
        summary = {
            "total_carbon": 0,
            "by_energy_type": {}
        }
        
        for energy_type, emission, consumption in results:
            summary["total_carbon"] += emission
            summary["by_energy_type"][energy_type] = {
                "carbon_emission": round(emission, 2),
                "energy_consumption": round(consumption, 2),
                "unit": EnergyService.ENERGY_UNITS.get(energy_type, "")
            }
        
        summary["total_carbon"] = round(summary["total_carbon"], 2)
        
        return summary
    
    @staticmethod
    def save_statistics(
        session: Session,
        device_id: Optional[int],
        energy_type: str,
        stat_time: datetime,
        period_type: str,
        stats: Dict
    ) -> EnergyStatistics:
        """
        保存统计数据
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            energy_type: 能源类型
            stat_time: 统计时间
            period_type: 统计周期
            stats: 统计数据字典
        """
        stat_record = EnergyStatistics(
            device_id=device_id,
            energy_type=energy_type,
            stat_time=stat_time,
            period_type=period_type,
            total_consumption=stats.get("total_consumption", 0),
            avg_flow_rate=stats.get("avg_flow_rate"),
            peak_flow_rate=stats.get("peak_flow_rate"),
            total_carbon=stats.get("total_carbon")
        )
        
        session.add(stat_record)
        session.commit()
        session.refresh(stat_record)
        
        return stat_record
