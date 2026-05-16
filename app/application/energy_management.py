"""
能源管理用例
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import Session

from app.application.analysis import get_energy_analysis_overview_use_case
from app.core.access_control import get_allowed_device_ids
from app.models.tables import CarbonEmission, EnergyData
from app.services.energy_service import EnergyService


ENERGY_OVERVIEW_TYPES = ("electricity", "water", "gas", "heat", "cooling", "steam")


def save_energy_data_use_case(
    session: Session,
    device_id: int,
    energy_type: str,
    consumption: float,
    flow_rate: Optional[float] = None,
    timestamp: Optional[datetime] = None,
    **kwargs: Any,
) -> EnergyData:
    """统一能源数据保存入口。"""
    return EnergyService.save_energy_data(
        session=session,
        device_id=device_id,
        energy_type=energy_type,
        consumption=consumption,
        flow_rate=flow_rate,
        timestamp=timestamp,
        **kwargs,
    )


def get_energy_statistics_use_case(
    session: Session,
    energy_type: str,
    start_time: datetime,
    end_time: datetime,
    device_id: Optional[int] = None,
    period_type: str = "day",
    allowed_device_ids: Optional[set[int]] = None,
) -> Dict[str, Any]:
    """统一能源统计入口。"""
    return EnergyService.calculate_statistics(
        session=session,
        device_id=device_id,
        energy_type=energy_type,
        start_time=start_time,
        end_time=end_time,
        period_type=period_type,
        allowed_device_ids=allowed_device_ids,
    )


def _normalize_analysis_for_energy_overview(analysis: dict) -> dict:
    """Expose the merged energy overview contract while keeping legacy analysis fields."""
    time_window = analysis.get("time_window") or {}
    trend = dict(analysis.get("trend") or {})
    trend_items = trend.get("items") or []
    trend["granularity"] = trend.get("granularity") or time_window.get("granularity")
    trend["points"] = trend.get("points") or [
        {
            "timestamp": item.get("timestamp"),
            "value": item.get("value", item.get("total_consumption", 0)),
            "load": item.get("load", item.get("total_load")),
        }
        for item in trend_items
    ]

    comparison = dict(analysis.get("comparison") or {})
    period = comparison.get("period_over_period") or {}
    energy_mix = comparison.get("energy_categories") or []
    comparison.setdefault("current", period.get("current_total_consumption", 0))
    comparison.setdefault("previous", period.get("previous_total_consumption", 0))
    comparison.setdefault("ratio", period.get("change_rate"))
    comparison.setdefault(
        "mix",
        [
            {
                "energy_type": item.get("energy_type", item.get("energy_category")),
                "share": item.get("share", item.get("ratio", 0)),
            }
            for item in energy_mix
        ],
    )

    ranking = dict(analysis.get("ranking") or {})
    ranking.setdefault("regions", ranking.get("regions", ranking.get("areas", [])))

    anomaly = dict(analysis.get("anomaly") or {})
    anomaly_summary = anomaly.get("summary") or {}
    anomaly.setdefault("missing_data", anomaly_summary.get("data_gap_count", 0))
    anomaly.setdefault("consecutive_failures", anomaly_summary.get("ingestion_failure_count", 0))
    anomaly.setdefault("unresolved_alarms", anomaly_summary.get("active_alarm_count", 0))

    insights = []
    for item in analysis.get("insights") or []:
        if isinstance(item, str):
            insights.append(item)
        else:
            title = item.get("title", "")
            detail = item.get("detail", "")
            insights.append(f"{title}：{detail}" if title and detail else title or detail)

    return {
        "time_window": time_window,
        "scope": analysis.get("scope"),
        "summary": analysis.get("summary"),
        "trend": trend,
        "comparison": comparison,
        "ranking": ranking,
        "anomaly": anomaly,
        "insights": insights,
    }


def get_energy_overview_use_case(
    session: Session,
    current_user,
    start_time: datetime,
    end_time: datetime,
    device_id: Optional[int] = None,
    location_id: Optional[int] = None,
    energy_type: Optional[str] = None,
    top_n: int = 5,
    granularity: str = "day",
    include_analysis: bool = True,
) -> dict:
    """统一多能源 overview 聚合入口。"""
    allowed_device_ids = get_allowed_device_ids(session, current_user)
    energy_types = list(ENERGY_OVERVIEW_TYPES)
    response: dict = {
        "statistics": EnergyService.get_statistics_by_type(
            session=session,
            start_time=start_time,
            end_time=end_time,
            device_id=device_id,
            energy_types=energy_types,
            allowed_device_ids=allowed_device_ids,
        ),
        "overview_boundary": "multi_energy_first_batch",
        "unit_rule": "累计量按时段首末差值统计；瞬时量按样本均值和峰值统计；不同能源不直接混算。",
        "cross_energy_mix_allowed": False,
        "field_boundary_rule": "consumption/flow_rate 属于公共层；其余 nullable 字段属于专属扩展层，不保证所有能源对象都适用。",
        "energy_profiles": {
            energy_type_value: EnergyService.get_energy_type_profile(energy_type_value)
            for energy_type_value in energy_types
        },
        "carbon_summary": EnergyService.get_carbon_summary(
            session=session,
            start_time=start_time,
            end_time=end_time,
            device_id=device_id,
            allowed_device_ids=allowed_device_ids,
        ),
    }

    if include_analysis:
        analysis = get_energy_analysis_overview_use_case(
            session=session,
            current_user=current_user,
            start_time=start_time,
            end_time=end_time,
            device_id=device_id,
            location_id=location_id,
            energy_type=energy_type,
            top_n=top_n,
            granularity=granularity,
        )
        response.update(_normalize_analysis_for_energy_overview(analysis))
    return response


def get_carbon_summary_use_case(
    session: Session,
    start_time: datetime,
    end_time: datetime,
    device_id: Optional[int] = None,
    allowed_device_ids: Optional[set[int]] = None,
) -> Dict[str, Any]:
    """统一碳排放汇总入口。"""
    return EnergyService.get_carbon_summary(
        session=session,
        start_time=start_time,
        end_time=end_time,
        device_id=device_id,
        allowed_device_ids=allowed_device_ids,
    )


def list_carbon_emissions_use_case(
    session: Session,
    device_id: Optional[int] = None,
    energy_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    allowed_device_ids: Optional[set[int]] = None,
) -> list[CarbonEmission]:
    """统一碳排放查询入口。"""
    return EnergyService.get_carbon_emissions(
        session=session,
        device_id=device_id,
        energy_type=energy_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        allowed_device_ids=allowed_device_ids,
    )
