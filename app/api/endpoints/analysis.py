"""
数据分析 API 端点。
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import get_current_user
from app.application.analysis import analyze_device_use_case, get_energy_analysis_overview_use_case
from app.core.database import get_session
from app.models.tables import User

router = APIRouter()


class TimeWindowResponse(BaseModel):
    start_time: datetime
    end_time: datetime
    granularity: str


class AnalysisScopeResponse(BaseModel):
    location_id: Optional[int] = None
    location_type: Optional[str] = None
    location_counts: dict[str, int]
    campus_entity_count: int
    energy_categories: list[str]
    sub_items: list[str]


class AnalysisSummaryResponse(BaseModel):
    total_consumption: float
    avg_load: float
    device_count: int
    active_device_count: int
    covered_energy_type_count: int
    covered_sub_item_count: int
    anomaly_count: int
    consumption_stat_basis: str


class TrendItemResponse(BaseModel):
    timestamp: datetime
    total_consumption: float
    total_load: float
    energy_breakdown: dict[str, float]


class TrendBlockResponse(BaseModel):
    items: list[TrendItemResponse]
    peak_load: Optional[TrendItemResponse] = None
    peak_consumption: Optional[TrendItemResponse] = None
    consumption_stat_basis: str


class ComparisonPeriodResponse(BaseModel):
    current_total_consumption: float
    previous_total_consumption: float
    delta_consumption: float
    change_rate: Optional[float] = None
    consumption_stat_basis: str


class EnergyCategoryComparisonItem(BaseModel):
    energy_category: str
    label: str
    total_consumption: float
    avg_load: float
    ratio: float


class SubItemComparisonItem(BaseModel):
    sub_item: str
    label: str
    total_consumption: float
    avg_load: float
    device_count: int
    energy_categories: list[str]


class ComparisonBlockResponse(BaseModel):
    period_over_period: ComparisonPeriodResponse
    energy_categories: list[EnergyCategoryComparisonItem]
    sub_items: list[SubItemComparisonItem]


class LocationRankingItemResponse(BaseModel):
    location_id: int
    name: str
    location_type: str
    full_path: Optional[str] = None
    total_consumption: float
    avg_load: float
    energy_breakdown: dict[str, float]


class DeviceRankingItemResponse(BaseModel):
    device_id: int
    name: str
    device_type: str
    device_category: str
    energy_type: str
    location: Optional[str] = None
    total_consumption: float
    avg_load: float


class RankingBlockResponse(BaseModel):
    areas: list[LocationRankingItemResponse]
    buildings: list[LocationRankingItemResponse]
    devices: list[DeviceRankingItemResponse]


class AnomalyItemResponse(BaseModel):
    kind: str
    severity: str
    device_id: int
    device_name: str
    device_type: str
    energy_type: str
    location: Optional[str] = None
    message: str
    detected_at: Optional[datetime] = None


class AnomalySummaryCountsResponse(BaseModel):
    total_count: int
    data_gap_count: int
    ingestion_failure_count: int
    active_alarm_count: int


class AnomalyBlockResponse(BaseModel):
    boundary: str
    summary: AnomalySummaryCountsResponse
    items: list[AnomalyItemResponse]


class InsightItemResponse(BaseModel):
    title: str
    detail: str
    severity: str
    dimension: str


class EnergyAnalysisOverviewResponse(BaseModel):
    time_window: TimeWindowResponse
    scope: AnalysisScopeResponse
    summary: AnalysisSummaryResponse
    trend: TrendBlockResponse
    comparison: ComparisonBlockResponse
    ranking: RankingBlockResponse
    anomaly: AnomalyBlockResponse
    insights: list[InsightItemResponse]


@router.get("/overview", response_model=EnergyAnalysisOverviewResponse)
def get_energy_analysis_overview(
    start_time: Optional[datetime] = Query(None, description="统计开始时间，默认最近 7 天"),
    end_time: Optional[datetime] = Query(None, description="统计结束时间，默认当前时间"),
    location_id: Optional[int] = Query(None, description="按园区/区域/楼栋位置收敛"),
    energy_type: Optional[str] = Query(None, description="按能源介质过滤"),
    top_n: int = Query(5, ge=3, le=20, description="排行与异常返回数量"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取能耗分析主页面第一批聚合结果。"""
    return get_energy_analysis_overview_use_case(
        session=session,
        current_user=current_user,
        start_time=start_time,
        end_time=end_time,
        location_id=location_id,
        energy_type=energy_type,
        top_n=top_n,
    )


@router.get("/{device_id}")
def analyze_device(
    device_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """获取设备数据分析。"""
    return analyze_device_use_case(session, current_user, device_id)
