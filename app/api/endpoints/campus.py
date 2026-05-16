"""
园区 EMS 聚合接口。
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import get_current_user
from app.application.campus import (
    get_alarm_summary_use_case,
    get_campus_overview_use_case,
    get_energy_category_share_use_case,
    get_location_energy_statistics_use_case,
    get_realtime_load_trend_use_case,
    get_subitem_statistics_use_case,
)
from app.core.database import get_session
from app.models.tables import User

router = APIRouter()


class TimeWindowResponse(BaseModel):
    start_time: datetime
    end_time: datetime


class CampusEntityResponse(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    location_type: str
    full_path: Optional[str] = None
    derived: bool = False


class AnalysisSummaryResponse(BaseModel):
    time_window: TimeWindowResponse
    total_consumption: float
    realtime_load: float
    active_alarm_count: int
    device_count: int
    meter_count: int
    building_count: int
    estimated_carbon: float


class EnergyCategorySummaryItem(BaseModel):
    energy_category: str
    label: str
    total_consumption: float
    avg_load: float
    ratio: float
    estimated_carbon: float


class SubItemStatisticsItem(BaseModel):
    sub_item: str
    label: str
    total_consumption: float
    avg_load: float
    device_count: int
    energy_categories: list[str]


class LocationRankingItem(BaseModel):
    location_id: int
    name: str
    location_type: str
    full_path: Optional[str] = None
    total_consumption: float
    avg_load: float
    energy_breakdown: dict[str, float]


class RealtimeLoadTrendItem(BaseModel):
    timestamp: datetime
    total_load: float
    total_consumption: float


class AlarmLatestItem(BaseModel):
    id: int
    device_id: int
    message: str
    severity: str
    category: str
    timestamp: datetime
    is_resolved: bool


class AlarmLocationItem(BaseModel):
    location_id: int
    name: str
    location_type: str
    alarm_count: int


class AlarmSummaryResponse(BaseModel):
    time_window: Optional[TimeWindowResponse] = None
    total_count: int
    unresolved_count: int
    resolved_count: int
    by_severity: dict[str, int]
    top_locations: list[AlarmLocationItem]
    latest: list[AlarmLatestItem]


class HierarchySummaryResponse(BaseModel):
    location_counts: dict[str, int]
    device_count: int
    active_device_count: int
    meter_count: int


class CampusOverviewResponse(BaseModel):
    campus_entities: list[CampusEntityResponse]
    hierarchy_summary: HierarchySummaryResponse
    analysis_summary: AnalysisSummaryResponse
    energy_category_summary: list[EnergyCategorySummaryItem]
    subitem_statistics: list[SubItemStatisticsItem]
    location_rankings: dict[str, list[LocationRankingItem]]
    realtime_load_trend: list[RealtimeLoadTrendItem]
    alarm_summary: AlarmSummaryResponse


class LocationEnergyStatisticsResponse(BaseModel):
    dimension: str
    time_window: TimeWindowResponse
    items: list[LocationRankingItem]


class EnergyCategoryShareResponse(BaseModel):
    time_window: TimeWindowResponse
    items: list[EnergyCategorySummaryItem]


class SubItemStatisticsResponse(BaseModel):
    time_window: TimeWindowResponse
    items: list[SubItemStatisticsItem]


class RealtimeLoadTrendResponse(BaseModel):
    time_window: TimeWindowResponse
    items: list[RealtimeLoadTrendItem]


def _call_use_case(use_case: Callable[..., dict], **kwargs):
    try:
        return use_case(**kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/overview", response_model=CampusOverviewResponse)
def get_campus_overview(
    start_time: Optional[datetime] = Query(None, description="统计开始时间，默认最近 24 小时"),
    end_time: Optional[datetime] = Query(None, description="统计结束时间，默认当前时间"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return _call_use_case(
        get_campus_overview_use_case,
        session=session,
        current_user=current_user,
        start_time=start_time,
        end_time=end_time,
    )


@router.get("/energy-statistics", response_model=LocationEnergyStatisticsResponse)
def get_location_energy_statistics(
    dimension: Literal["area", "building"] = Query("area", description="统计维度：area/building"),
    start_time: Optional[datetime] = Query(None, description="统计开始时间，默认最近 30 天"),
    end_time: Optional[datetime] = Query(None, description="统计结束时间，默认当前时间"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return _call_use_case(
        get_location_energy_statistics_use_case,
        session=session,
        current_user=current_user,
        dimension=dimension,
        start_time=start_time,
        end_time=end_time,
    )


@router.get("/energy-categories", response_model=EnergyCategoryShareResponse)
def get_energy_category_share(
    start_time: Optional[datetime] = Query(None, description="统计开始时间，默认最近 30 天"),
    end_time: Optional[datetime] = Query(None, description="统计结束时间，默认当前时间"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return _call_use_case(
        get_energy_category_share_use_case,
        session=session,
        current_user=current_user,
        start_time=start_time,
        end_time=end_time,
    )


@router.get("/subitems", response_model=SubItemStatisticsResponse)
def get_subitem_statistics(
    start_time: Optional[datetime] = Query(None, description="统计开始时间，默认最近 30 天"),
    end_time: Optional[datetime] = Query(None, description="统计结束时间，默认当前时间"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return _call_use_case(
        get_subitem_statistics_use_case,
        session=session,
        current_user=current_user,
        start_time=start_time,
        end_time=end_time,
    )


@router.get("/realtime-load-trend", response_model=RealtimeLoadTrendResponse)
def get_realtime_load_trend(
    start_time: Optional[datetime] = Query(None, description="统计开始时间，默认最近 24 小时"),
    end_time: Optional[datetime] = Query(None, description="统计结束时间，默认当前时间"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return _call_use_case(
        get_realtime_load_trend_use_case,
        session=session,
        current_user=current_user,
        start_time=start_time,
        end_time=end_time,
    )


@router.get("/alarms/summary", response_model=AlarmSummaryResponse)
def get_alarm_summary(
    start_time: Optional[datetime] = Query(None, description="统计开始时间，默认最近 24 小时"),
    end_time: Optional[datetime] = Query(None, description="统计结束时间，默认当前时间"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return _call_use_case(
        get_alarm_summary_use_case,
        session=session,
        current_user=current_user,
        start_time=start_time,
        end_time=end_time,
    )
