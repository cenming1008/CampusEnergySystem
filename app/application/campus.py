"""
园区聚合接口主流程 use case。
"""

from __future__ import annotations

from datetime import datetime

from sqlmodel import Session

from app.core.access_control import get_allowed_device_ids
from app.services.campus_service import CampusService


def _resolve_window(
    start_time: datetime | None,
    end_time: datetime | None,
    default_hours: int,
) -> tuple[datetime, datetime]:
    return CampusService.normalize_time_window(start_time, end_time, default_hours)


def _allowed_device_ids(session: Session, current_user):
    return get_allowed_device_ids(session, current_user)


def get_campus_overview_use_case(
    session: Session,
    current_user,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> dict:
    window_start, window_end = _resolve_window(start_time, end_time, 24)
    return CampusService.get_campus_overview(
        session=session,
        start_time=window_start,
        end_time=window_end,
        allowed_device_ids=_allowed_device_ids(session, current_user),
    )


def get_location_energy_statistics_use_case(
    session: Session,
    current_user,
    dimension: str = "area",
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> dict:
    window_start, window_end = _resolve_window(start_time, end_time, 24 * 30)
    return CampusService.get_location_energy_statistics(
        session=session,
        dimension=dimension,
        start_time=window_start,
        end_time=window_end,
        allowed_device_ids=_allowed_device_ids(session, current_user),
    )


def get_energy_category_share_use_case(
    session: Session,
    current_user,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> dict:
    window_start, window_end = _resolve_window(start_time, end_time, 24 * 30)
    return CampusService.get_energy_category_share(
        session=session,
        start_time=window_start,
        end_time=window_end,
        allowed_device_ids=_allowed_device_ids(session, current_user),
    )


def get_subitem_statistics_use_case(
    session: Session,
    current_user,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> dict:
    window_start, window_end = _resolve_window(start_time, end_time, 24 * 30)
    return CampusService.get_subitem_statistics(
        session=session,
        start_time=window_start,
        end_time=window_end,
        allowed_device_ids=_allowed_device_ids(session, current_user),
    )


def get_realtime_load_trend_use_case(
    session: Session,
    current_user,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> dict:
    window_start, window_end = _resolve_window(start_time, end_time, 24)
    return CampusService.get_realtime_load_trend(
        session=session,
        start_time=window_start,
        end_time=window_end,
        allowed_device_ids=_allowed_device_ids(session, current_user),
    )


def get_alarm_summary_use_case(
    session: Session,
    current_user,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> dict:
    window_start, window_end = _resolve_window(start_time, end_time, 24)
    return CampusService.get_alarm_summary(
        session=session,
        start_time=window_start,
        end_time=window_end,
        allowed_device_ids=_allowed_device_ids(session, current_user),
    )
