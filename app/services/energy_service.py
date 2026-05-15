"""
能源数据服务（编排层）

职责：
- 调 domain 层的纯业务规则（电价、统计、碳排放因子、语义、校验）
- 调 repository 层的数据访问
- 处理副作用（日志、commit）

业务规则在 app/domain/energy_rules.py，数据查询在 app/repositories/energy_repository.py。
"""
from datetime import datetime
from typing import Dict, List, Optional

from sqlmodel import Session

from app.core.device_registry import device_registry
from app.core.logger import logger
from app.domain import energy_rules
from app.domain.device_payloads import describe_energy_data_fields
from app.domain.energy_rules import (
    CARBON_FACTORS as DOMAIN_CARBON_FACTORS,
    ENERGY_DISPLAY_LABELS as DOMAIN_ENERGY_DISPLAY_LABELS,
    ENERGY_PRICES as DOMAIN_ENERGY_PRICES,
    ENERGY_UNITS as DOMAIN_ENERGY_UNITS,
    build_carbon_fields,
    calculate_energy_cost as calculate_energy_cost_rule,
    empty_energy_statistics,
    get_carbon_factor,
    get_electricity_price as get_electricity_price_rule,
    get_energy_semantics,
    summarize_carbon_by_energy_type,
    summarize_energy_statistics,
    summarize_multi_energy_statistics,
    validate_energy_type_match,
)
from app.models.tables import (
    CarbonEmission,
    EnergyData,
    EnergyStatistics,
    EnergyType,
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
    """能源数据服务（编排层）。"""

    # 常量保留以保持向后兼容（domain 层的 re-export）
    CARBON_FACTORS = DOMAIN_CARBON_FACTORS
    ENERGY_UNITS = DOMAIN_ENERGY_UNITS
    ENERGY_LABELS = DOMAIN_ENERGY_DISPLAY_LABELS
    ENERGY_PRICES = DOMAIN_ENERGY_PRICES

    # ==================== 语义查询（domain pass-through） ====================

    @staticmethod
    def get_energy_semantics(energy_type: str) -> Dict:
        """返回第一批多能源业务语义。"""
        return dict(get_energy_semantics(energy_type))

    @staticmethod
    def list_energy_type_catalog() -> list[Dict]:
        """返回多能源类型与第一批语义说明。"""
        return [
            {
                **EnergyService.get_energy_semantics(energy_type.value),
                "supported_device_types": [
                    config.device_type
                    for config in device_registry.get_by_energy_type(energy_type)
                ],
            }
            for energy_type in EnergyType
        ]

    @staticmethod
    def get_energy_type_profile(energy_type: str) -> Dict:
        semantics = EnergyService.get_energy_semantics(energy_type)
        device_configs = device_registry.get_by_energy_type(EnergyType(energy_type))
        specialized_fields = sorted({
            field
            for config in device_configs
            for field in config.specialized_fields
        })
        return {
            **semantics,
            "supported_device_types": [config.device_type for config in device_configs],
            "supported_device_categories": sorted({config.category.value for config in device_configs}),
            "field_profiles": [
                describe_energy_data_fields(config.device_type)
                for config in device_configs
            ],
            "data_object_kind": "energy_point_series",
            "point_kind": "energy_point_series",
            "public_fields": ["consumption", "flow_rate", "timestamp"],
            "specialized_fields": specialized_fields,
            "null_field_rule": "nullable_specialized_field_means_not_applicable_or_not_reported",
        }

    @staticmethod
    def get_electricity_price(hour: int) -> float:
        """根据时段获取电价（峰谷平电价）。"""
        return get_electricity_price_rule(hour)

    @staticmethod
    def calculate_energy_cost(
        energy_type: str,
        consumption: float,
        timestamp: datetime,
    ) -> float:
        """计算能源成本。"""
        return calculate_energy_cost_rule(energy_type, consumption, timestamp)

    # ==================== 编排：保存能源数据 ====================

    @staticmethod
    def save_energy_data(
        session: Session,
        device_id: int,
        energy_type: str,
        consumption: float,
        flow_rate: Optional[float] = None,
        timestamp: Optional[datetime] = None,
        **kwargs,
    ) -> EnergyData:
        """保存能源数据，并自动计算碳排放（同事务）。"""
        if timestamp is None:
            timestamp = datetime.now()

        # 校验设备 + 类型一致性（业务规则下沉到 domain）
        device = DeviceRepository.get_by_id(session, device_id)
        if not device:
            raise ValueError(f"设备 {device_id} 不存在")
        try:
            validate_energy_type_match(device.energy_type, energy_type)
        except ValueError as exc:
            raise ValueError(f"设备 {device_id} {exc}") from exc

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

        # 自动计算并保存碳排放，与能耗记录同事务
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

        logger.debug(
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
        """计算并保存碳排放数据。"""
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

        logger.debug(
            f"计算碳排放: 设备={device_id}, 排放={carbon_emission_value:.2f} kg CO2"
        )
        return carbon_record

    # ==================== 编排：查询接口 ====================

    @staticmethod
    def get_energy_data(
        session: Session,
        device_id: int,
        energy_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[EnergyData]:
        """查询能源数据。"""
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
        """查询碳排放数据。"""
        return EnergyRepository.list_carbon_emissions(
            session,
            device_id=device_id,
            energy_type=energy_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            allowed_device_ids=allowed_device_ids,
        )

    # ==================== 编排：统计计算 ====================

    @staticmethod
    def _build_statistics_for_type(
        session: Session,
        energy_type: str,
        start_time: datetime,
        end_time: datetime,
        device_id: Optional[int] = None,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> Dict:
        """单一能源类型的统计计算（含语义增强）。"""
        rows = EnergyRepository.list_energy_statistics_rows(
            session,
            device_id=device_id,
            energy_type=energy_type,
            start_time=start_time,
            end_time=end_time,
            allowed_device_ids=allowed_device_ids,
        )
        if rows:
            result = summarize_energy_statistics(rows)
        else:
            result = empty_energy_statistics(energy_type)

        profile = EnergyService.get_energy_type_profile(energy_type)
        result.update({
            "data_object_kind": profile["data_object_kind"],
            "point_kind": profile["point_kind"],
            "public_fields": profile["public_fields"],
            "specialized_fields": profile["specialized_fields"],
            "null_field_rule": profile["null_field_rule"],
        })
        return result

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
        """计算能源统计数据。"""
        return EnergyService._build_statistics_for_type(
            session,
            energy_type=energy_type,
            start_time=start_time,
            end_time=end_time,
            device_id=device_id,
            allowed_device_ids=allowed_device_ids,
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
        """按能源类型分组返回统计结果。"""
        results: Dict[str, Dict] = {}
        for energy_type in energy_types:
            stats = EnergyService._build_statistics_for_type(
                session,
                energy_type=energy_type,
                start_time=start_time,
                end_time=end_time,
                device_id=device_id,
                allowed_device_ids=allowed_device_ids,
            )
            profile = EnergyService.get_energy_type_profile(energy_type)
            stats["supported_device_types"] = profile["supported_device_types"]
            results[energy_type] = stats
        return results

    @staticmethod
    def get_carbon_summary(
        session: Session,
        start_time: datetime,
        end_time: datetime,
        device_id: Optional[int] = None,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> Dict:
        """获取碳排放汇总。"""
        rows: list[tuple[str, float, float]] = []
        for energy_type in EnergyType:
            samples = EnergyRepository.list_energy_statistics_rows(
                session,
                device_id=device_id,
                energy_type=energy_type.value,
                start_time=start_time,
                end_time=end_time,
                allowed_device_ids=allowed_device_ids,
            )
            stats = summarize_multi_energy_statistics(samples).get(energy_type.value)
            if not stats or not stats["data_count"]:
                continue
            carbon_factor = get_carbon_factor(energy_type.value)
            rows.append((
                energy_type.value,
                stats["total_consumption"] * carbon_factor,
                stats["total_consumption"],
            ))

        summary = summarize_carbon_by_energy_type(rows)
        summary["summary_basis"] = "energy_period_delta"
        return summary

    @staticmethod
    def get_analysis_overview(
        session: Session,
        start_time: datetime,
        end_time: datetime,
        allowed_device_ids: Optional[set[int]] = None,
        device_id: Optional[int] = None,
        location_id: Optional[int] = None,
        energy_type: Optional[str] = None,
        top_n: int = 5,
        granularity: Optional[str] = None,
    ) -> Dict:
        """能源总览页分析字段聚合入口。"""
        from app.services.analysis_service import AnalysisService

        return AnalysisService.get_energy_analysis_overview(
            session=session,
            start_time=start_time,
            end_time=end_time,
            allowed_device_ids=allowed_device_ids,
            device_id=device_id,
            location_id=location_id,
            energy_type=energy_type,
            top_n=top_n,
            granularity=granularity,
        )

    @staticmethod
    def save_statistics(
        session: Session,
        device_id: Optional[int],
        energy_type: str,
        stat_time: datetime,
        period_type: str,
        stats: Dict,
    ) -> EnergyStatistics:
        """保存统计数据。"""
        stat_record = EnergyStatistics(
            device_id=device_id,
            energy_type=energy_type,
            stat_time=stat_time,
            period_type=period_type,
            total_consumption=stats.get("total_consumption", 0),
            avg_flow_rate=stats.get("avg_flow_rate"),
            peak_flow_rate=stats.get("peak_flow_rate"),
            total_carbon=stats.get("total_carbon"),
        )
        return EnergyRepository.save_statistics_record(session, stat_record)
