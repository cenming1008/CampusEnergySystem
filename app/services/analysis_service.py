"""
数据分析服务（编排层）

职责：
- 调 domain 层（analysis_rules + energy_rules + device_payloads）的纯规则
- 调 repository 层（analysis_repository + energy_repository + device_repository）的数据访问
- 处理副作用 / 编排聚合调用

业务规则在 app/domain/analysis_rules.py，数据查询在 app/repositories/analysis_repository.py。
"""
from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Any, Dict, Optional

from sqlmodel import Session

from app.domain import analysis_rules
from app.domain.campus_rules import ENERGY_CATEGORY_LABELS
from app.domain.device_payloads import describe_device_type_semantics, describe_energy_data_fields
from app.domain.energy_rules import calculate_energy_cost, get_energy_semantics
from app.models.tables import EnergyData
from app.repositories.analysis_repository import AnalysisRepository
from app.repositories.device_repository import DeviceRepository
from app.repositories.energy_repository import EnergyRepository
from app.services.campus_service import (
    AREA_LOCATION_TYPES,
    BUILDING_LOCATION_TYPES,
    CampusService,
    SITE_LOCATION_TYPES,
    SUB_ITEM_LABELS,
)


class AnalysisService:
    """数据分析服务（编排层）。"""

    @staticmethod
    def analyze_device(session: Session, device_id: int) -> Dict[str, Any]:
        """分析单台设备的最新数据与今日能耗/费用。"""
        device = DeviceRepository.get_by_id(session, device_id)
        is_active = device.is_active if device else False
        energy_type = device.energy_type if device else "electricity"
        semantics = get_energy_semantics(energy_type)
        device_type_semantics = (
            describe_device_type_semantics(device.device_type) if device else {}
        )

        latest = EnergyRepository.get_latest_energy_data(
            session, device_id, energy_type=energy_type,
        )
        if not latest:
            return AnalysisService._empty_analysis(
                is_active,
                energy_type,
                semantics,
                device_type=device.device_type if device else None,
                device_category=device.device_category if device else None,
                device_type_semantics=device_type_semantics,
            )

        today_consumption, today_cost = AnalysisService._calculate_today_consumption(
            session, device_id, energy_type, latest,
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
    def _calculate_today_consumption(
        session: Session,
        device_id: int,
        energy_type: str,
        latest: EnergyData,
    ) -> tuple[float, float]:
        """计算今日累计能耗与费用（峰谷平电价估算）。"""
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

    @staticmethod
    def get_energy_analysis_overview(
        session: Session,
        start_time: datetime,
        end_time: datetime,
        allowed_device_ids: Optional[set[int]] = None,
        device_id: Optional[int] = None,
        location_id: Optional[int] = None,
        energy_type: Optional[str] = None,
        top_n: int = 5,
        granularity: Optional[str] = None,
    ) -> Dict[str, Any]:
        """返回能耗分析主页面第一批聚合数据。"""
        # 1. 解析作用域设备 ID
        base_context = CampusService.build_context(session, allowed_device_ids)
        scoped_device_ids = AnalysisService._resolve_scope_device_ids(base_context, location_id)
        if allowed_device_ids is not None:
            scoped_device_ids &= allowed_device_ids
        if device_id is not None:
            scoped_device_ids &= {device_id}
        if energy_type:
            scoped_device_ids = {
                device.id
                for device in base_context.devices
                if device.id in scoped_device_ids and device.energy_type == energy_type
            }

        context = CampusService.build_context(session, scoped_device_ids)

        # 2. 查询数据（repository 层）
        current_rows = AnalysisRepository.list_energy_rows(
            session=session,
            start_time=start_time,
            end_time=end_time,
            allowed_device_ids=scoped_device_ids,
            energy_type=energy_type,
        )
        window_duration = max(end_time - start_time, timedelta(hours=1))
        previous_rows = AnalysisRepository.list_energy_rows(
            session=session,
            start_time=start_time - window_duration,
            end_time=start_time,
            allowed_device_ids=scoped_device_ids,
            energy_type=energy_type,
        )
        unresolved_alarm_rows = AnalysisRepository.list_unresolved_alarm_rows(
            session, scoped_device_ids,
        )
        health_rows = AnalysisRepository.list_health_rows(session, scoped_device_ids)

        # 3. 调用 domain 层做聚合
        current_device_stats = analysis_rules.build_device_statistics(current_rows)
        previous_device_stats = analysis_rules.build_device_statistics(previous_rows)
        trend_granularity = granularity or analysis_rules.resolve_trend_granularity(
            start_time, end_time,
        )

        comparison = analysis_rules.build_comparison(
            current_device_stats=current_device_stats,
            previous_device_stats=previous_device_stats,
            device_by_id=context.device_by_id,
            energy_category_labels=ENERGY_CATEGORY_LABELS,
            sub_item_labels=SUB_ITEM_LABELS,
        )
        ranking = {
            "areas": analysis_rules.build_location_rankings(
                device_stats=current_device_stats,
                device_by_id=context.device_by_id,
                locations_by_id=context.locations_by_id,
                target_types=AREA_LOCATION_TYPES,
                top_n=top_n,
                find_ancestor=CampusService._find_ancestor_location,
            ),
            "buildings": analysis_rules.build_location_rankings(
                device_stats=current_device_stats,
                device_by_id=context.device_by_id,
                locations_by_id=context.locations_by_id,
                target_types=BUILDING_LOCATION_TYPES,
                top_n=top_n,
                find_ancestor=CampusService._find_ancestor_location,
            ),
            "devices": analysis_rules.build_device_rankings(
                device_stats=current_device_stats,
                device_by_id=context.device_by_id,
                locations_by_id=context.locations_by_id,
                top_n=top_n,
            ),
        }
        anomaly = analysis_rules.build_anomaly_summary(
            health_rows=health_rows,
            unresolved_alarm_rows=unresolved_alarm_rows,
            device_by_id=context.device_by_id,
            locations_by_id=context.locations_by_id,
            end_time=end_time,
            top_n=top_n,
        )
        summary = analysis_rules.build_summary(
            devices=context.devices,
            device_by_id=context.device_by_id,
            device_stats=current_device_stats,
            anomaly_summary=anomaly["summary"],
        )
        trend_items = analysis_rules.build_trend_items(
            current_rows=current_rows,
            device_by_id=context.device_by_id,
            granularity=trend_granularity,
        )

        return {
            "time_window": {
                "start_time": start_time,
                "end_time": end_time,
                "granularity": trend_granularity,
            },
            "scope": analysis_rules.build_scope_summary(
                devices=context.devices,
                locations_by_id=context.locations_by_id,
                relevant_location_ids=context.relevant_location_ids,
                site_location_types=SITE_LOCATION_TYPES,
                location_id=location_id,
                energy_type=energy_type,
            ),
            "summary": summary,
            "trend": {
                "items": trend_items,
                "peak_load": max(trend_items, key=lambda item: item["total_load"], default=None),
                "peak_consumption": max(
                    trend_items,
                    key=lambda item: item["total_consumption"],
                    default=None,
                ),
                "consumption_stat_basis": "period_delta_from_cumulative_reading",
            },
            "comparison": comparison,
            "ranking": ranking,
            "anomaly": anomaly,
            "insights": analysis_rules.build_insights(
                comparison=comparison,
                ranking=ranking,
                anomaly=anomaly,
                summary=summary,
            ),
        }

    @staticmethod
    def _resolve_scope_device_ids(base_context, location_id: Optional[int]) -> set[int]:
        """根据 location_id 收敛设备集合。"""
        scoped_ids = {device.id for device in base_context.devices if device.id is not None}
        if location_id is None:
            return scoped_ids

        result: set[int] = set()
        for device in base_context.devices:
            if device.id is None or device.location_id is None:
                continue
            if analysis_rules.location_is_within(
                locations_by_id=base_context.locations_by_id,
                candidate_id=device.location_id,
                target_id=location_id,
            ):
                result.add(device.id)
        return result
