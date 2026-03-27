"""
园区 EMS 聚合接口。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session

from app.api.deps import get_current_user
from app.core.access_control import get_allowed_device_ids
from app.core.database import get_session
from app.models.tables import User
from app.services.campus_service import CampusService

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


def _resolve_window(
    start_time: Optional[datetime],
    end_time: Optional[datetime],
    default_hours: int,
) -> tuple[datetime, datetime]:
    return CampusService.normalize_time_window(start_time, end_time, default_hours)


@router.get("/overview", response_model=CampusOverviewResponse)
def get_campus_overview(
    start_time: Optional[datetime] = Query(None, description="统计开始时间，默认最近 24 小时"),
    end_time: Optional[datetime] = Query(None, description="统计结束时间，默认当前时间"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    window_start, window_end = _resolve_window(start_time, end_time, default_hours=24)
    return CampusService.get_campus_overview(
        session=session,
        start_time=window_start,
        end_time=window_end,
        allowed_device_ids=get_allowed_device_ids(session, current_user),
    )


@router.get("/energy-statistics", response_model=LocationEnergyStatisticsResponse)
def get_location_energy_statistics(
    dimension: Literal["area", "building"] = Query("area", description="统计维度：area/building"),
    start_time: Optional[datetime] = Query(None, description="统计开始时间，默认最近 30 天"),
    end_time: Optional[datetime] = Query(None, description="统计结束时间，默认当前时间"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    window_start, window_end = _resolve_window(start_time, end_time, default_hours=24 * 30)
    return CampusService.get_location_energy_statistics(
        session=session,
        dimension=dimension,
        start_time=window_start,
        end_time=window_end,
        allowed_device_ids=get_allowed_device_ids(session, current_user),
    )


@router.get("/energy-categories", response_model=EnergyCategoryShareResponse)
def get_energy_category_share(
    start_time: Optional[datetime] = Query(None, description="统计开始时间，默认最近 30 天"),
    end_time: Optional[datetime] = Query(None, description="统计结束时间，默认当前时间"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    window_start, window_end = _resolve_window(start_time, end_time, default_hours=24 * 30)
    return CampusService.get_energy_category_share(
        session=session,
        start_time=window_start,
        end_time=window_end,
        allowed_device_ids=get_allowed_device_ids(session, current_user),
    )


@router.get("/subitems", response_model=SubItemStatisticsResponse)
def get_subitem_statistics(
    start_time: Optional[datetime] = Query(None, description="统计开始时间，默认最近 30 天"),
    end_time: Optional[datetime] = Query(None, description="统计结束时间，默认当前时间"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    window_start, window_end = _resolve_window(start_time, end_time, default_hours=24 * 30)
    return CampusService.get_subitem_statistics(
        session=session,
        start_time=window_start,
        end_time=window_end,
        allowed_device_ids=get_allowed_device_ids(session, current_user),
    )


@router.get("/realtime-load-trend", response_model=RealtimeLoadTrendResponse)
def get_realtime_load_trend(
    start_time: Optional[datetime] = Query(None, description="统计开始时间，默认最近 24 小时"),
    end_time: Optional[datetime] = Query(None, description="统计结束时间，默认当前时间"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    window_start, window_end = _resolve_window(start_time, end_time, default_hours=24)
    return CampusService.get_realtime_load_trend(
        session=session,
        start_time=window_start,
        end_time=window_end,
        allowed_device_ids=get_allowed_device_ids(session, current_user),
    )


@router.get("/alarms/summary", response_model=AlarmSummaryResponse)
def get_alarm_summary(
    start_time: Optional[datetime] = Query(None, description="统计开始时间，默认最近 24 小时"),
    end_time: Optional[datetime] = Query(None, description="统计结束时间，默认当前时间"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    window_start, window_end = _resolve_window(start_time, end_time, default_hours=24)
    return CampusService.get_alarm_summary(
        session=session,
        start_time=window_start,
        end_time=window_end,
        allowed_device_ids=get_allowed_device_ids(session, current_user),
    )
