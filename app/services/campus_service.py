"""
园区 EMS 聚合服务。

基于现有 Location / Device / EnergyData / Alarm 等底座模型，
提供面向园区驾驶舱与园区空间主线的兼容聚合能力。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from app.domain.campus_rules import (
    SITE_LOCATION_TYPES,
    build_alarm_summary,
    build_energy_category_summary,
    build_hierarchy_summary,
    build_location_rankings,
    build_period_energy_summaries,
    build_realtime_load_trend,
    build_site_entities,
    build_subitem_statistics,
)
from app.models.tables import Alarm, Device, EnergyData, Location

AREA_LOCATION_TYPES = {"area", "zone"}
BUILDING_LOCATION_TYPES = {"building"}

@dataclass
class CampusContext:
    locations_by_id: dict[int, Location]
    devices: list[Device]
    device_by_id: dict[int, Device]
    relevant_location_ids: set[int]


class CampusService:
    """园区 EMS 聚合服务。"""

    @staticmethod
    def build_context(
        session: Session,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> CampusContext:
        locations = list(session.exec(select(Location)).all())
        devices_statement = select(Device)
        if allowed_device_ids is not None:
            if not allowed_device_ids:
                return CampusContext(
                    locations_by_id={location.id: location for location in locations if location.id is not None},
                    devices=[],
                    device_by_id={},
                    relevant_location_ids=set(),
                )
            devices_statement = devices_statement.where(Device.id.in_(allowed_device_ids))

        devices = list(session.exec(devices_statement).all())
        locations_by_id = {location.id: location for location in locations if location.id is not None}
        relevant_location_ids = CampusService._collect_relevant_location_ids(locations_by_id, devices)
        return CampusContext(
            locations_by_id=locations_by_id,
            devices=devices,
            device_by_id={device.id: device for device in devices if device.id is not None},
            relevant_location_ids=relevant_location_ids,
        )

    @staticmethod
    def normalize_time_window(
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        default_hours: int,
    ) -> tuple[datetime, datetime]:
        end = end_time or datetime.now()
        start = start_time or (end - timedelta(hours=default_hours))
        if start > end:
            raise ValueError("start_time 不能晚于 end_time")
        return start, end

    @staticmethod
    def get_campus_overview(
        session: Session,
        start_time: datetime,
        end_time: datetime,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> dict:
        context = CampusService.build_context(session, allowed_device_ids)
        energy_rows = CampusService._list_energy_rows(session, start_time, end_time, allowed_device_ids)
        period_summaries = build_period_energy_summaries(energy_rows)
        trend_rows = CampusService._list_energy_rows(
            session,
            end_time - timedelta(hours=24),
            end_time,
            allowed_device_ids,
        )
        alarm_rows = CampusService._list_alarm_rows(session, start_time, end_time, allowed_device_ids)

        hierarchy_summary = build_hierarchy_summary(
            context.locations_by_id,
            context.relevant_location_ids,
            context.devices,
        )
        energy_category_summary = build_energy_category_summary(period_summaries)
        subitem_statistics = build_subitem_statistics(period_summaries, context.device_by_id)
        area_rankings = build_location_rankings(
            period_summaries,
            context.device_by_id,
            context.locations_by_id,
            AREA_LOCATION_TYPES,
            top_n=5,
            find_ancestor=CampusService._find_ancestor_location,
        )
        building_rankings = build_location_rankings(
            period_summaries,
            context.device_by_id,
            context.locations_by_id,
            BUILDING_LOCATION_TYPES,
            top_n=5,
            find_ancestor=CampusService._find_ancestor_location,
        )
        realtime_load_trend = build_realtime_load_trend(trend_rows)
        alarm_summary = build_alarm_summary(
            alarm_rows,
            context.device_by_id,
            context.locations_by_id,
            AREA_LOCATION_TYPES | BUILDING_LOCATION_TYPES,
            find_ancestor=CampusService._find_ancestor_location,
        )

        latest_load = realtime_load_trend[-1]["total_load"] if realtime_load_trend else 0.0
        total_consumption = sum(item["total_consumption"] for item in energy_category_summary)
        total_carbon = sum(item["estimated_carbon"] for item in energy_category_summary)

        return {
            "campus_entities": build_site_entities(context.locations_by_id, context.relevant_location_ids),
            "hierarchy_summary": hierarchy_summary,
            "analysis_summary": {
                "time_window": {
                    "start_time": start_time,
                    "end_time": end_time,
                },
                "total_consumption": round(total_consumption, 3),
                "realtime_load": round(latest_load, 3),
                "active_alarm_count": alarm_summary["unresolved_count"],
                "device_count": hierarchy_summary["device_count"],
                "meter_count": hierarchy_summary["meter_count"],
                "building_count": hierarchy_summary["location_counts"]["building"],
                "estimated_carbon": round(total_carbon, 3),
            },
            "energy_category_summary": energy_category_summary,
            "subitem_statistics": subitem_statistics,
            "location_rankings": {
                "areas": area_rankings,
                "buildings": building_rankings,
            },
            "realtime_load_trend": realtime_load_trend,
            "alarm_summary": alarm_summary,
        }

    @staticmethod
    def get_location_energy_statistics(
        session: Session,
        dimension: str,
        start_time: datetime,
        end_time: datetime,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> dict:
        context = CampusService.build_context(session, allowed_device_ids)
        target_types = AREA_LOCATION_TYPES if dimension == "area" else BUILDING_LOCATION_TYPES
        rows = CampusService._list_energy_rows(session, start_time, end_time, allowed_device_ids)
        period_summaries = build_period_energy_summaries(rows)
        rankings = build_location_rankings(
            period_summaries,
            context.device_by_id,
            context.locations_by_id,
            target_types,
            top_n=20,
            find_ancestor=CampusService._find_ancestor_location,
        )
        return {
            "dimension": dimension,
            "time_window": {
                "start_time": start_time,
                "end_time": end_time,
            },
            "items": rankings,
        }

    @staticmethod
    def get_energy_category_share(
        session: Session,
        start_time: datetime,
        end_time: datetime,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> dict:
        rows = CampusService._list_energy_rows(session, start_time, end_time, allowed_device_ids)
        period_summaries = build_period_energy_summaries(rows)
        return {
            "time_window": {"start_time": start_time, "end_time": end_time},
            "items": build_energy_category_summary(period_summaries),
        }

    @staticmethod
    def get_subitem_statistics(
        session: Session,
        start_time: datetime,
        end_time: datetime,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> dict:
        context = CampusService.build_context(session, allowed_device_ids)
        rows = CampusService._list_energy_rows(session, start_time, end_time, allowed_device_ids)
        period_summaries = build_period_energy_summaries(rows)
        return {
            "time_window": {"start_time": start_time, "end_time": end_time},
            "items": build_subitem_statistics(period_summaries, context.device_by_id),
        }

    @staticmethod
    def get_realtime_load_trend(
        session: Session,
        start_time: datetime,
        end_time: datetime,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> dict:
        rows = CampusService._list_energy_rows(session, start_time, end_time, allowed_device_ids)
        return {
            "time_window": {"start_time": start_time, "end_time": end_time},
            "items": build_realtime_load_trend(rows),
        }

    @staticmethod
    def get_alarm_summary(
        session: Session,
        start_time: datetime,
        end_time: datetime,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> dict:
        context = CampusService.build_context(session, allowed_device_ids)
        rows = CampusService._list_alarm_rows(session, start_time, end_time, allowed_device_ids)
        summary = build_alarm_summary(
            rows,
            context.device_by_id,
            context.locations_by_id,
            AREA_LOCATION_TYPES | BUILDING_LOCATION_TYPES,
            find_ancestor=CampusService._find_ancestor_location,
        )
        summary["time_window"] = {"start_time": start_time, "end_time": end_time}
        return summary

    @staticmethod
    def _collect_relevant_location_ids(
        locations_by_id: dict[int, Location],
        devices: Iterable[Device],
    ) -> set[int]:
        relevant_location_ids: set[int] = set()
        for device in devices:
            location_id = device.location_id
            while location_id is not None and location_id not in relevant_location_ids:
                relevant_location_ids.add(location_id)
                parent = locations_by_id.get(location_id)
                location_id = parent.parent_id if parent else None
        return relevant_location_ids

    @staticmethod
    def _list_energy_rows(
        session: Session,
        start_time: datetime,
        end_time: datetime,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> list[EnergyData]:
        statement = (
            select(EnergyData)
            .where(EnergyData.timestamp >= start_time)
            .where(EnergyData.timestamp <= end_time)
            .order_by(EnergyData.timestamp.asc())
        )
        if allowed_device_ids is not None:
            if not allowed_device_ids:
                return []
            statement = statement.where(EnergyData.device_id.in_(allowed_device_ids))
        return list(session.exec(statement).all())

    @staticmethod
    def _list_alarm_rows(
        session: Session,
        start_time: datetime,
        end_time: datetime,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> list[Alarm]:
        statement = (
            select(Alarm)
            .where(Alarm.timestamp >= start_time)
            .where(Alarm.timestamp <= end_time)
            .order_by(Alarm.timestamp.desc())
        )
        if allowed_device_ids is not None:
            if not allowed_device_ids:
                return []
            statement = statement.where(Alarm.device_id.in_(allowed_device_ids))
        return list(session.exec(statement).all())

    @staticmethod
    def _find_ancestor_location(
        locations_by_id: dict[int, Location],
        location_id: int,
        target_types: set[str],
    ) -> Optional[Location]:
        current_id = location_id
        while current_id is not None:
            location = locations_by_id.get(current_id)
            if not location:
                return None
            if location.location_type in target_types:
                return location
            current_id = location.parent_id
        return None
