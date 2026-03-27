"""
能源数据服务 - 处理多种能源类型的数据采集和分析
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlmodel import Session, select, func
from app.core.logger import logger

from app.domain.energy_rules import (
    CARBON_FACTORS as DOMAIN_CARBON_FACTORS,
    ENERGY_PRICES as DOMAIN_ENERGY_PRICES,
    ENERGY_UNITS as DOMAIN_ENERGY_UNITS,
    build_carbon_fields,
    calculate_energy_cost as calculate_energy_cost_rule,
    get_electricity_price as get_electricity_price_rule,
    summarize_carbon_by_energy_type,
    summarize_energy_statistics,
)
from app.models.tables import (
    Device, EnergyData, CarbonEmission, EnergyStatistics,
    EnergyType
)
from app.repositories.device_repository import DeviceRepository
from app.repositories.energy_repository import EnergyRepository


def _collect_energy_fields(
    energy_type: str,
    consumption: float,
    flow_rate: Optional[float],
    kwargs: Dict,
) -> Dict:
    """统一收集 EnergyData 可写字段。"""
    fields = {
        "energy_type": energy_type,
        "consumption": consumption,
        "flow_rate": flow_rate,
    }
    fields.update(kwargs)
    return fields


def _collect_carbon_fields(
    energy_type: str,
    consumption: float,
) -> Dict:
    """统一收集 CarbonEmission 可写字段。"""
    return dict(build_carbon_fields(energy_type, consumption))


class EnergyService:
    """能源数据服务类"""
    
    # 碳排放因子 (kg CO2 / 单位)
    CARBON_FACTORS = DOMAIN_CARBON_FACTORS
    
    # 能源单位映射
    ENERGY_UNITS = DOMAIN_ENERGY_UNITS
    
    # 能源价格（元/单位）- 可根据实际情况调整
    ENERGY_PRICES = DOMAIN_ENERGY_PRICES
    
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
        return get_electricity_price_rule(hour)
    
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
        return calculate_energy_cost_rule(energy_type, consumption, timestamp)
    
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
        device = DeviceRepository.get_by_id(session, device_id)
        if not device:
            raise ValueError(f"设备 {device_id} 不存在")
        
        if device.energy_type != energy_type:
            raise ValueError(
                f"设备 {device_id} 能源类型不匹配: "
                f"期望 {device.energy_type}, 实际 {energy_type}"
            )

        energy_fields = _collect_energy_fields(energy_type, consumption, flow_rate, kwargs)
        energy_data = EnergyRepository.get_energy_record(session, device_id, timestamp)
        is_update = energy_data is not None
        if energy_data:
            for field, value in energy_fields.items():
                setattr(energy_data, field, value)
        else:
            energy_data = EnergyData(
                device_id=device_id,
                timestamp=timestamp,
                **energy_fields,
            )
            EnergyRepository.save_energy_record(session, energy_data, commit=False)

        # 自动计算并保存碳排放，和能耗记录同事务提交
        EnergyService.calculate_carbon_emission(
            session,
            device_id,
            energy_type,
            consumption,
            timestamp,
            auto_commit=False,
        )

        session.commit()
        session.refresh(energy_data)
        
        logger.info(
            f"保存能源数据: 设备={device_id}, 类型={energy_type}, "
            f"消耗={consumption}, 时间={timestamp}, 模式={'update' if is_update else 'insert'}"
        )
        
        return energy_data
    
    @staticmethod
    def calculate_carbon_emission(
        session: Session,
        device_id: int,
        energy_type: str,
        consumption: float,
        timestamp: datetime,
        auto_commit: bool = True,
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
        carbon_fields = _collect_carbon_fields(energy_type, consumption)
        carbon_emission_value = carbon_fields["carbon_emission"]
        carbon_record = EnergyRepository.get_carbon_record(session, device_id, timestamp)
        if carbon_record:
            for field, value in carbon_fields.items():
                setattr(carbon_record, field, value)
        else:
            carbon_record = CarbonEmission(
                device_id=device_id,
                timestamp=timestamp,
                **carbon_fields,
            )
            EnergyRepository.save_carbon_record(session, carbon_record, commit=False)

        if auto_commit:
            session.commit()
        else:
            session.flush()

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
        return EnergyRepository.list_energy_data(
            session,
            device_id=device_id,
            energy_type=energy_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
    
    @staticmethod
    def get_carbon_emissions(
        session: Session,
        device_id: Optional[int] = None,
        energy_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        allowed_device_ids: Optional[set[int]] = None,
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
        return EnergyRepository.list_carbon_emissions(
            session,
            device_id=device_id,
            energy_type=energy_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            allowed_device_ids=allowed_device_ids,
        )
    
    @staticmethod
    def calculate_statistics(
        session: Session,
        device_id: Optional[int],
        energy_type: str,
        start_time: datetime,
        end_time: datetime,
        period_type: str = "day",
        allowed_device_ids: Optional[set[int]] = None,
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
        return summarize_energy_statistics(
            EnergyRepository.list_energy_statistics_rows(
                session,
                device_id=device_id,
                energy_type=energy_type,
                start_time=start_time,
                end_time=end_time,
                allowed_device_ids=allowed_device_ids,
            )
        )

    @staticmethod
    def get_statistics_by_type(
        session: Session,
        start_time: datetime,
        end_time: datetime,
        energy_types: list[str],
        device_id: Optional[int] = None,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> Dict[str, Dict]:
        defaults = {
            "total_consumption": 0.0,
            "avg_consumption": 0.0,
            "avg_flow_rate": 0.0,
            "peak_flow_rate": 0.0,
            "data_count": 0,
        }
        results = {energy_type: dict(defaults) for energy_type in energy_types}
        rows = EnergyRepository.summarize_energy_statistics_by_type(
            session,
            start_time=start_time,
            end_time=end_time,
            device_id=device_id,
            allowed_device_ids=allowed_device_ids,
            energy_types=energy_types,
        )
        for energy_type, total, avg_consumption, avg_flow_rate, peak_flow_rate, data_count in rows:
            results[str(energy_type)] = {
                "total_consumption": float(total or 0),
                "avg_consumption": float(avg_consumption or 0),
                "avg_flow_rate": float(avg_flow_rate or 0),
                "peak_flow_rate": float(peak_flow_rate or 0),
                "data_count": int(data_count or 0),
            }
        return results
    
    @staticmethod
    def get_carbon_summary(
        session: Session,
        start_time: datetime,
        end_time: datetime,
        device_id: Optional[int] = None,
        allowed_device_ids: Optional[set[int]] = None,
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
        return summarize_carbon_by_energy_type(
            EnergyRepository.summarize_carbon_rows(
                session,
                start_time=start_time,
                end_time=end_time,
                device_id=device_id,
                allowed_device_ids=allowed_device_ids,
            )
        )
    
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
        
        return EnergyRepository.save_statistics_record(session, stat_record)
