"""
数据分析服务层
封装数据分析相关的业务逻辑
"""
from collections import defaultdict
from datetime import datetime, time, timedelta
from typing import Any, Dict, Optional

from sqlmodel import Session, select

from app.domain.device_payloads import describe_device_type_semantics, describe_energy_data_fields
from app.domain.energy_rules import calculate_energy_cost, get_energy_semantics, summarize_energy_statistics
from app.models.tables import Alarm, Device, DeviceIngestionHealth, EnergyData, Location
from app.repositories.device_repository import DeviceRepository
from app.repositories.energy_repository import EnergyRepository
from app.services.campus_service import (
    AREA_LOCATION_TYPES,
    BUILDING_LOCATION_TYPES,
    CampusService,
    ENERGY_CATEGORY_LABELS,
    SITE_LOCATION_TYPES,
    SUB_ITEM_LABELS,
)


class AnalysisService:
    """数据分析服务类"""

    @staticmethod
    def analyze_device(session: Session, device_id: int) -> Dict[str, Any]:
        """分析设备数据"""
        # 获取设备状态
        device = DeviceRepository.get_by_id(session, device_id)
        is_active = device.is_active if device else False
        energy_type = device.energy_type if device else "electricity"
        semantics = get_energy_semantics(energy_type)
        device_type_semantics = describe_device_type_semantics(device.device_type) if device else {}

        # 获取最新数据
        latest = AnalysisService._get_latest_data(session, device_id, energy_type)
        if not latest:
            return AnalysisService._empty_analysis(
                is_active,
                energy_type,
                semantics,
                device_type=device.device_type if device else None,
                device_category=device.device_category if device else None,
                device_type_semantics=device_type_semantics,
            )

        # 计算当日消耗与费用
        today_consumption, today_cost = AnalysisService._calculate_today_consumption(
            session, device_id, energy_type, latest
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
    def _get_latest_data(
        session: Session,
        device_id: int,
        energy_type: Optional[str] = None,
    ) -> Optional[EnergyData]:
        """获取设备最新数据"""
        return EnergyRepository.get_latest_energy_data(session, device_id, energy_type=energy_type)
    
    @staticmethod
    def _calculate_today_consumption(
        session: Session,
        device_id: int,
        energy_type: str,
        latest: EnergyData
    ) -> tuple[float, float]:
        """
        计算今日能耗和费用（使用峰谷平电价）
        
        注意：这里简化处理，使用当前时段的电价估算总费用。
        更精确的方法是逐小时计算，但会增加复杂度。
        """
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
        """返回空数据分析结果"""
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
        location_id: Optional[int] = None,
        energy_type: Optional[str] = None,
        top_n: int = 5,
    ) -> Dict[str, Any]:
        """返回能耗分析主页面第一批聚合数据。"""
        base_context = CampusService.build_context(session, allowed_device_ids)
        scoped_device_ids = AnalysisService._resolve_scope_device_ids(base_context, location_id)
        if allowed_device_ids is not None:
            scoped_device_ids &= allowed_device_ids
        if energy_type:
            scoped_device_ids = {
                device.id
                for device in base_context.devices
                if device.id in scoped_device_ids and device.energy_type == energy_type
            }

        context = CampusService.build_context(session, scoped_device_ids)
        current_rows = AnalysisService._list_energy_rows(
            session=session,
            start_time=start_time,
            end_time=end_time,
            allowed_device_ids=scoped_device_ids,
            energy_type=energy_type,
        )
        window_duration = max(end_time - start_time, timedelta(hours=1))
        previous_rows = AnalysisService._list_energy_rows(
            session=session,
            start_time=start_time - window_duration,
            end_time=start_time,
            allowed_device_ids=scoped_device_ids,
            energy_type=energy_type,
        )
        current_device_stats = AnalysisService._build_device_statistics(current_rows)
        previous_device_stats = AnalysisService._build_device_statistics(previous_rows)
        unresolved_alarm_rows = AnalysisService._list_unresolved_alarm_rows(session, scoped_device_ids)
        health_rows = AnalysisService._list_health_rows(session, scoped_device_ids)
        granularity = AnalysisService._resolve_trend_granularity(start_time, end_time)

        comparison = AnalysisService._build_comparison(
            current_device_stats=current_device_stats,
            previous_device_stats=previous_device_stats,
            device_by_id=context.device_by_id,
        )
        ranking = {
            "areas": AnalysisService._build_location_rankings(
                context=context,
                device_stats=current_device_stats,
                target_types=AREA_LOCATION_TYPES,
                top_n=top_n,
            ),
            "buildings": AnalysisService._build_location_rankings(
                context=context,
                device_stats=current_device_stats,
                target_types=BUILDING_LOCATION_TYPES,
                top_n=top_n,
            ),
            "devices": AnalysisService._build_device_rankings(
                device_stats=current_device_stats,
                device_by_id=context.device_by_id,
                locations_by_id=context.locations_by_id,
                top_n=top_n,
            ),
        }
        anomaly = AnalysisService._build_anomaly_summary(
            context=context,
            health_rows=health_rows,
            unresolved_alarm_rows=unresolved_alarm_rows,
            end_time=end_time,
            top_n=top_n,
        )
        summary = AnalysisService._build_summary(
            context=context,
            device_stats=current_device_stats,
            anomaly_summary=anomaly["summary"],
        )
        trend_items = AnalysisService._build_trend_items(
            current_rows=current_rows,
            device_by_id=context.device_by_id,
            granularity=granularity,
        )

        return {
            "time_window": {
                "start_time": start_time,
                "end_time": end_time,
                "granularity": granularity,
            },
            "scope": AnalysisService._build_scope_summary(
                context=context,
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
            "insights": AnalysisService._build_insights(
                comparison=comparison,
                ranking=ranking,
                anomaly=anomaly,
                summary=summary,
            ),
        }

    @staticmethod
    def _resolve_scope_device_ids(base_context, location_id: Optional[int]) -> set[int]:
        scoped_ids = {device.id for device in base_context.devices if device.id is not None}
        if location_id is None:
            return scoped_ids

        result: set[int] = set()
        for device in base_context.devices:
            if device.id is None or device.location_id is None:
                continue
            if AnalysisService._location_is_within(
                locations_by_id=base_context.locations_by_id,
                candidate_id=device.location_id,
                target_id=location_id,
            ):
                result.add(device.id)
        return result

    @staticmethod
    def _location_is_within(
        locations_by_id: Dict[int, Location],
        candidate_id: int,
        target_id: int,
    ) -> bool:
        current_id = candidate_id
        while current_id is not None:
            if current_id == target_id:
                return True
            location = locations_by_id.get(current_id)
            if location is None:
                return False
            current_id = location.parent_id
        return False

    @staticmethod
    def _list_energy_rows(
        session: Session,
        start_time: datetime,
        end_time: datetime,
        allowed_device_ids: Optional[set[int]],
        energy_type: Optional[str] = None,
    ) -> list[EnergyData]:
        if allowed_device_ids is not None and not allowed_device_ids:
            return []
        statement = (
            select(EnergyData)
            .where(EnergyData.timestamp >= start_time)
            .where(EnergyData.timestamp <= end_time)
            .order_by(EnergyData.timestamp.asc())
        )
        if allowed_device_ids is not None:
            statement = statement.where(EnergyData.device_id.in_(allowed_device_ids))
        if energy_type:
            statement = statement.where(EnergyData.energy_type == energy_type)
        return list(session.exec(statement).all())

    @staticmethod
    def _list_health_rows(session: Session, allowed_device_ids: Optional[set[int]]) -> list[DeviceIngestionHealth]:
        if allowed_device_ids is not None and not allowed_device_ids:
            return []
        statement = select(DeviceIngestionHealth)
        if allowed_device_ids is not None:
            statement = statement.where(DeviceIngestionHealth.device_id.in_(allowed_device_ids))
        return list(session.exec(statement).all())

    @staticmethod
    def _list_unresolved_alarm_rows(session: Session, allowed_device_ids: Optional[set[int]]) -> list[Alarm]:
        if allowed_device_ids is not None and not allowed_device_ids:
            return []
        statement = (
            select(Alarm)
            .where(Alarm.is_resolved == False)  # noqa: E712
            .order_by(Alarm.timestamp.desc())
        )
        if allowed_device_ids is not None:
            statement = statement.where(Alarm.device_id.in_(allowed_device_ids))
        return list(session.exec(statement).all())

    @staticmethod
    def _build_device_statistics(rows: list[EnergyData]) -> Dict[int, Dict[str, Any]]:
        grouped_rows: Dict[int, list[EnergyData]] = defaultdict(list)
        for row in rows:
            grouped_rows[row.device_id].append(row)

        results: Dict[int, Dict[str, Any]] = {}
        for device_id, device_rows in grouped_rows.items():
            stats = summarize_energy_statistics(device_rows)
            results[device_id] = {
                "total_consumption": float(stats["total_consumption"]),
                "avg_load": float(stats["avg_flow_rate"]),
                "peak_load": float(stats["peak_flow_rate"]),
                "data_count": int(stats["data_count"]),
                "energy_type": device_rows[-1].energy_type,
                "last_timestamp": device_rows[-1].timestamp,
                "meter_reset_suspected": bool(stats.get("meter_reset_suspected", False)),
            }
        return results

    @staticmethod
    def _resolve_trend_granularity(start_time: datetime, end_time: datetime) -> str:
        return "hour" if end_time - start_time <= timedelta(hours=48) else "day"

    @staticmethod
    def _bucket_timestamp(timestamp: datetime, granularity: str) -> datetime:
        if granularity == "hour":
            return timestamp.replace(minute=0, second=0, microsecond=0)
        return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def _build_trend_items(
        current_rows: list[EnergyData],
        device_by_id: Dict[int, Device],
        granularity: str,
    ) -> list[Dict[str, Any]]:
        buckets: Dict[datetime, list[EnergyData]] = defaultdict(list)
        for row in current_rows:
            buckets[AnalysisService._bucket_timestamp(row.timestamp, granularity)].append(row)

        items: list[Dict[str, Any]] = []
        for timestamp, bucket_rows in sorted(buckets.items(), key=lambda item: item[0]):
            device_stats = AnalysisService._build_device_statistics(bucket_rows)
            energy_breakdown: Dict[str, float] = defaultdict(float)
            total_consumption = 0.0
            total_load = 0.0
            for device_id, stats in device_stats.items():
                device = device_by_id.get(device_id)
                current_energy_type = device.energy_type if device and device.energy_type else stats["energy_type"]
                total_consumption += stats["total_consumption"]
                total_load += stats["avg_load"]
                energy_breakdown[current_energy_type] += stats["total_consumption"]
            items.append(
                {
                    "timestamp": timestamp,
                    "total_consumption": round(total_consumption, 3),
                    "total_load": round(total_load, 3),
                    "energy_breakdown": {
                        key: round(value, 3)
                        for key, value in sorted(
                            energy_breakdown.items(),
                            key=lambda item: item[1],
                            reverse=True,
                        )
                    },
                }
            )
        return items

    @staticmethod
    def _build_comparison(
        current_device_stats: Dict[int, Dict[str, Any]],
        previous_device_stats: Dict[int, Dict[str, Any]],
        device_by_id: Dict[int, Device],
    ) -> Dict[str, Any]:
        current_total = sum(item["total_consumption"] for item in current_device_stats.values())
        previous_total = sum(item["total_consumption"] for item in previous_device_stats.values())
        delta = current_total - previous_total
        change_rate = (delta / previous_total) if previous_total else None
        return {
            "period_over_period": {
                "current_total_consumption": round(current_total, 3),
                "previous_total_consumption": round(previous_total, 3),
                "delta_consumption": round(delta, 3),
                "change_rate": round(change_rate, 4) if change_rate is not None else None,
                "consumption_stat_basis": "period_delta_from_cumulative_reading",
            },
            "energy_categories": AnalysisService._build_energy_category_summary(
                device_stats=current_device_stats,
                device_by_id=device_by_id,
            ),
            "sub_items": AnalysisService._build_subitem_statistics(
                device_stats=current_device_stats,
                device_by_id=device_by_id,
            )[:5],
        }

    @staticmethod
    def _build_energy_category_summary(
        device_stats: Dict[int, Dict[str, Any]],
        device_by_id: Dict[int, Device],
    ) -> list[Dict[str, Any]]:
        aggregates: Dict[str, Dict[str, float]] = defaultdict(lambda: {"consumption": 0.0, "load": 0.0})
        total_consumption = 0.0
        for device_id, stats in device_stats.items():
            device = device_by_id.get(device_id)
            current_energy_type = device.energy_type if device and device.energy_type else stats["energy_type"]
            aggregates[current_energy_type]["consumption"] += stats["total_consumption"]
            aggregates[current_energy_type]["load"] += stats["avg_load"]
            total_consumption += stats["total_consumption"]

        items = []
        for current_energy_type, value in sorted(
            aggregates.items(),
            key=lambda item: item[1]["consumption"],
            reverse=True,
        ):
            consumption = round(value["consumption"], 3)
            items.append(
                {
                    "energy_category": current_energy_type,
                    "label": ENERGY_CATEGORY_LABELS.get(current_energy_type, current_energy_type),
                    "total_consumption": consumption,
                    "avg_load": round(value["load"], 3),
                    "ratio": round(consumption / total_consumption, 4) if total_consumption else 0.0,
                }
            )
        return items

    @staticmethod
    def _build_subitem_statistics(
        device_stats: Dict[int, Dict[str, Any]],
        device_by_id: Dict[int, Device],
    ) -> list[Dict[str, Any]]:
        items: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"consumption": 0.0, "load": 0.0, "device_ids": set(), "energy_categories": set()}
        )
        for device_id, stats in device_stats.items():
            device = device_by_id.get(device_id)
            if not device:
                continue
            sub_item = device.device_category or device.device_type or "device"
            item = items[sub_item]
            item["consumption"] += stats["total_consumption"]
            item["load"] += stats["avg_load"]
            item["device_ids"].add(device_id)
            item["energy_categories"].add(device.energy_type or stats["energy_type"])

        results = []
        for sub_item, value in sorted(items.items(), key=lambda item: item[1]["consumption"], reverse=True):
            results.append(
                {
                    "sub_item": sub_item,
                    "label": SUB_ITEM_LABELS.get(sub_item, sub_item),
                    "total_consumption": round(value["consumption"], 3),
                    "avg_load": round(value["load"], 3),
                    "device_count": len(value["device_ids"]),
                    "energy_categories": sorted(value["energy_categories"]),
                }
            )
        return results

    @staticmethod
    def _build_location_rankings(
        context,
        device_stats: Dict[int, Dict[str, Any]],
        target_types: set[str],
        top_n: int,
    ) -> list[Dict[str, Any]]:
        aggregates: Dict[int, Dict[str, Any]] = defaultdict(
            lambda: {"consumption": 0.0, "load": 0.0, "energy_breakdown": defaultdict(float)}
        )
        for device_id, stats in device_stats.items():
            device = context.device_by_id.get(device_id)
            if not device or device.location_id is None:
                continue
            target = CampusService._find_ancestor_location(
                context.locations_by_id,
                device.location_id,
                target_types,
            )
            if target is None:
                continue
            item = aggregates[target.id]
            item["consumption"] += stats["total_consumption"]
            item["load"] += stats["avg_load"]
            item["energy_breakdown"][device.energy_type or stats["energy_type"]] += stats["total_consumption"]

        results = []
        for current_location_id, value in aggregates.items():
            location = context.locations_by_id.get(current_location_id)
            if not location:
                continue
            results.append(
                {
                    "location_id": location.id,
                    "name": location.name,
                    "location_type": location.location_type,
                    "full_path": location.full_path,
                    "total_consumption": round(value["consumption"], 3),
                    "avg_load": round(value["load"], 3),
                    "energy_breakdown": {
                        key: round(amount, 3)
                        for key, amount in sorted(
                            value["energy_breakdown"].items(),
                            key=lambda item: item[1],
                            reverse=True,
                        )
                    },
                }
            )
        results.sort(key=lambda item: item["total_consumption"], reverse=True)
        return results[:top_n]

    @staticmethod
    def _build_device_rankings(
        device_stats: Dict[int, Dict[str, Any]],
        device_by_id: Dict[int, Device],
        locations_by_id: Dict[int, Location],
        top_n: int,
    ) -> list[Dict[str, Any]]:
        items = []
        for device_id, stats in device_stats.items():
            device = device_by_id.get(device_id)
            if not device:
                continue
            location_name = device.location
            if device.location_id is not None:
                location = locations_by_id.get(device.location_id)
                if location:
                    location_name = location.full_path or location.name
            items.append(
                {
                    "device_id": device.id,
                    "name": device.name,
                    "device_type": device.device_type,
                    "device_category": device.device_category,
                    "energy_type": device.energy_type or stats["energy_type"],
                    "location": location_name,
                    "total_consumption": round(stats["total_consumption"], 3),
                    "avg_load": round(stats["avg_load"], 3),
                }
            )
        items.sort(key=lambda item: item["total_consumption"], reverse=True)
        return items[:top_n]

    @staticmethod
    def _build_anomaly_summary(
        context,
        health_rows: list[DeviceIngestionHealth],
        unresolved_alarm_rows: list[Alarm],
        end_time: datetime,
        top_n: int,
    ) -> Dict[str, Any]:
        items = []
        data_gap_count = 0
        failure_count = 0

        for health in health_rows:
            device = context.device_by_id.get(health.device_id)
            if not device:
                continue
            if health.last_message_at is None:
                data_gap_count += 1
                items.append(
                    AnalysisService._build_anomaly_item(
                        kind="data_gap",
                        severity="critical",
                        device=device,
                        locations_by_id=context.locations_by_id,
                        message="设备暂无接入报文，无法形成稳定分析走势。",
                        detected_at=health.updated_at,
                    )
                )
                continue

            if end_time - health.last_message_at > timedelta(hours=2):
                data_gap_count += 1
                items.append(
                    AnalysisService._build_anomaly_item(
                        kind="data_gap",
                        severity="warning",
                        device=device,
                        locations_by_id=context.locations_by_id,
                        message=f"最近报文停留在 {health.last_message_at:%Y-%m-%d %H:%M}，存在数据断档风险。",
                        detected_at=health.last_message_at,
                    )
                )
            elif health.consecutive_failures >= 3:
                failure_count += 1
                items.append(
                    AnalysisService._build_anomaly_item(
                        kind="ingestion_failure",
                        severity="warning",
                        device=device,
                        locations_by_id=context.locations_by_id,
                        message=health.last_failure_reason or "设备接入连续失败，需要排查采集链路。",
                        detected_at=health.last_failure_at or health.updated_at,
                    )
                )

        active_alarm_count = 0
        for alarm in unresolved_alarm_rows:
            device = context.device_by_id.get(alarm.device_id)
            if not device:
                continue
            active_alarm_count += 1
            items.append(
                AnalysisService._build_anomaly_item(
                    kind="active_alarm",
                    severity=alarm.severity,
                    device=device,
                    locations_by_id=context.locations_by_id,
                    message=alarm.message,
                    detected_at=alarm.last_seen_at or alarm.timestamp,
                )
            )

        severity_order = {"critical": 0, "warning": 1, "info": 2}
        items.sort(
            key=lambda item: (
                severity_order.get(item["severity"], 99),
                -(item["detected_at"].timestamp() if item["detected_at"] else 0),
            )
        )
        return {
            "boundary": "operational_signal_first_batch",
            "summary": {
                "total_count": len(items[:top_n]),
                "data_gap_count": data_gap_count,
                "ingestion_failure_count": failure_count,
                "active_alarm_count": active_alarm_count,
            },
            "items": items[:top_n],
        }

    @staticmethod
    def _build_anomaly_item(
        kind: str,
        severity: str,
        device: Device,
        locations_by_id: Dict[int, Location],
        message: str,
        detected_at: Optional[datetime],
    ) -> Dict[str, Any]:
        location_name = device.location
        if device.location_id is not None:
            location = locations_by_id.get(device.location_id)
            if location:
                location_name = location.full_path or location.name
        return {
            "kind": kind,
            "severity": severity,
            "device_id": device.id,
            "device_name": device.name,
            "device_type": device.device_type,
            "energy_type": device.energy_type,
            "location": location_name,
            "message": message,
            "detected_at": detected_at,
        }

    @staticmethod
    def _build_scope_summary(context, location_id: Optional[int], energy_type: Optional[str]) -> Dict[str, Any]:
        location_counts = {
            "park": 0,
            "campus": 0,
            "site": 0,
            "area": 0,
            "zone": 0,
            "building": 0,
        }
        for current_location_id in context.relevant_location_ids:
            location = context.locations_by_id.get(current_location_id)
            if location and location.location_type in location_counts:
                location_counts[location.location_type] += 1

        return {
            "location_id": location_id,
            "location_type": AnalysisService._resolve_scope_location_type(context.locations_by_id, location_id),
            "location_counts": location_counts,
            "campus_entity_count": sum(location_counts[key] for key in SITE_LOCATION_TYPES if key in location_counts),
            "energy_categories": sorted(
                {
                    device.energy_type
                    for device in context.devices
                    if device.energy_type and (energy_type is None or device.energy_type == energy_type)
                }
            ),
            "sub_items": sorted(
                {
                    device.device_category or device.device_type
                    for device in context.devices
                    if device.device_category or device.device_type
                }
            ),
        }

    @staticmethod
    def _resolve_scope_location_type(
        locations_by_id: Dict[int, Location],
        location_id: Optional[int],
    ) -> Optional[str]:
        if location_id is None:
            return None
        location = locations_by_id.get(location_id)
        return location.location_type if location else None

    @staticmethod
    def _build_summary(
        context,
        device_stats: Dict[int, Dict[str, Any]],
        anomaly_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        total_consumption = sum(item["total_consumption"] for item in device_stats.values())
        avg_load = sum(item["avg_load"] for item in device_stats.values())
        return {
            "total_consumption": round(total_consumption, 3),
            "avg_load": round(avg_load, 3),
            "device_count": len(context.devices),
            "active_device_count": sum(1 for device in context.devices if device.is_active),
            "covered_energy_type_count": len(
                {
                    (context.device_by_id.get(device_id).energy_type if context.device_by_id.get(device_id) else stats["energy_type"])
                    for device_id, stats in device_stats.items()
                }
            ),
            "covered_sub_item_count": len(
                {
                    device.device_category or device.device_type
                    for device in context.devices
                    if device.device_category or device.device_type
                }
            ),
            "anomaly_count": anomaly_summary["total_count"],
            "consumption_stat_basis": "period_delta_from_cumulative_reading",
        }

    @staticmethod
    def _build_insights(
        comparison: Dict[str, Any],
        ranking: Dict[str, Any],
        anomaly: Dict[str, Any],
        summary: Dict[str, Any],
    ) -> list[Dict[str, Any]]:
        insights = []
        energy_categories = comparison.get("energy_categories", [])
        if energy_categories:
            dominant = energy_categories[0]
            insights.append(
                {
                    "title": f"{dominant['label']} 仍是当前主导能源",
                    "detail": f"本周期 {dominant['label']} 累计占比 {dominant['ratio'] * 100:.1f}%，可优先用于趋势和节能动作跟踪。",
                    "severity": "info",
                    "dimension": "energy_type",
                }
            )

        change_rate = comparison.get("period_over_period", {}).get("change_rate")
        if change_rate is not None:
            insights.append(
                {
                    "title": f"总能耗环比{'上升' if change_rate > 0 else '下降'}",
                    "detail": f"当前周期较上一周期变化 {change_rate * 100:.1f}%，可结合区域和分项排行继续定位来源。",
                    "severity": "warning" if change_rate > 0.1 else "info",
                    "dimension": "comparison",
                }
            )

        areas = ranking.get("areas") or []
        top_area = areas[0] if areas else None
        if top_area:
            insights.append(
                {
                    "title": f"{top_area['name']} 是当前高消耗区域",
                    "detail": f"该区域累计消耗 {top_area['total_consumption']:.2f}，适合作为下一步区域级分析和巡检联动的优先对象。",
                    "severity": "info",
                    "dimension": "area",
                }
            )

        if anomaly["summary"]["total_count"]:
            insights.append(
                {
                    "title": "当前存在待跟进异常信号",
                    "detail": f"已识别 {anomaly['summary']['total_count']} 条运营异常信号，当前以接入断档和未恢复告警为主。",
                    "severity": "warning",
                    "dimension": "anomaly",
                }
            )

        if not insights:
            insights.append(
                {
                    "title": "当前分析窗口暂无明显波动",
                    "detail": f"已覆盖 {summary['device_count']} 台设备，可继续扩大真实采集覆盖后再提升对比和异常精度。",
                    "severity": "info",
                    "dimension": "summary",
                }
            )
        return insights[:4]
