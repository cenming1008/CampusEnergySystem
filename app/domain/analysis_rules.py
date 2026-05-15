"""
能耗分析领域规则：聚合统计、趋势分桶、排行、异常识别、洞察生成。

所有函数为纯函数，不依赖数据库或 I/O。输入为已加载的 ORM 模型集合，
输出为结构化字典或 dataclass。
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, Optional

from app.domain.energy_rules import summarize_energy_statistics
from app.models.tables import Alarm, Device, DeviceIngestionHealth, EnergyData, Location


# ==================== 通用纯工具 ====================


def location_is_within(
    locations_by_id: Dict[int, Location],
    candidate_id: int,
    target_id: int,
) -> bool:
    """判断候选位置是否在目标位置的层级树内（含自身）。"""
    current_id = candidate_id
    while current_id is not None:
        if current_id == target_id:
            return True
        location = locations_by_id.get(current_id)
        if location is None:
            return False
        current_id = location.parent_id
    return False


def resolve_scope_location_type(
    locations_by_id: Dict[int, Location],
    location_id: Optional[int],
) -> Optional[str]:
    """获取指定位置的层级类型。"""
    if location_id is None:
        return None
    location = locations_by_id.get(location_id)
    return location.location_type if location else None


def resolve_trend_granularity(start_time: datetime, end_time: datetime) -> str:
    """根据时间窗口大小决定趋势分桶粒度。"""
    return "hour" if end_time - start_time <= timedelta(hours=48) else "day"


def bucket_timestamp(timestamp: datetime, granularity: str) -> datetime:
    """将时间戳按粒度分桶。"""
    if granularity == "hour":
        return timestamp.replace(minute=0, second=0, microsecond=0)
    return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)


# ==================== 设备级统计 ====================


def build_device_statistics(rows: Iterable[EnergyData]) -> Dict[int, Dict[str, Any]]:
    """按设备分组聚合 EnergyData 行，复用 energy_rules 的统计函数。"""
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


# ==================== 趋势分桶 ====================


def build_trend_items(
    current_rows: list[EnergyData],
    device_by_id: Dict[int, Device],
    granularity: str,
) -> list[Dict[str, Any]]:
    """按粒度分桶并聚合每个时间桶的负荷与消耗。"""
    buckets: Dict[datetime, list[EnergyData]] = defaultdict(list)
    for row in current_rows:
        buckets[bucket_timestamp(row.timestamp, granularity)].append(row)

    items: list[Dict[str, Any]] = []
    for timestamp, bucket_rows in sorted(buckets.items(), key=lambda item: item[0]):
        device_stats = build_device_statistics(bucket_rows)
        energy_breakdown: Dict[str, float] = defaultdict(float)
        total_consumption = 0.0
        total_load = 0.0
        for device_id, stats in device_stats.items():
            device = device_by_id.get(device_id)
            current_energy_type = (
                device.energy_type if device and device.energy_type else stats["energy_type"]
            )
            total_consumption += stats["total_consumption"]
            total_load += stats["avg_load"]
            energy_breakdown[current_energy_type] += stats["total_consumption"]
        items.append({
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
        })
    return items


# ==================== 对比与分类汇总 ====================


def build_comparison(
    current_device_stats: Dict[int, Dict[str, Any]],
    previous_device_stats: Dict[int, Dict[str, Any]],
    device_by_id: Dict[int, Device],
    energy_category_labels: Dict[str, str],
    sub_item_labels: Dict[str, str],
) -> Dict[str, Any]:
    """构造期间对比、能源分类聚合、分项 Top 5。"""
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
        "energy_categories": build_energy_category_summary(
            current_device_stats, device_by_id, energy_category_labels,
        ),
        "sub_items": build_subitem_statistics(
            current_device_stats, device_by_id, sub_item_labels,
        )[:5],
    }


def build_energy_category_summary(
    device_stats: Dict[int, Dict[str, Any]],
    device_by_id: Dict[int, Device],
    energy_category_labels: Dict[str, str],
) -> list[Dict[str, Any]]:
    """按能源类型聚合消耗、负荷、占比。"""
    aggregates: Dict[str, Dict[str, float]] = defaultdict(
        lambda: {"consumption": 0.0, "load": 0.0}
    )
    total_consumption = 0.0
    for device_id, stats in device_stats.items():
        device = device_by_id.get(device_id)
        current_energy_type = (
            device.energy_type if device and device.energy_type else stats["energy_type"]
        )
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
        items.append({
            "energy_category": current_energy_type,
            "label": energy_category_labels.get(current_energy_type, current_energy_type),
            "total_consumption": consumption,
            "avg_load": round(value["load"], 3),
            "ratio": round(consumption / total_consumption, 4) if total_consumption else 0.0,
        })
    return items


def build_subitem_statistics(
    device_stats: Dict[int, Dict[str, Any]],
    device_by_id: Dict[int, Device],
    sub_item_labels: Dict[str, str],
) -> list[Dict[str, Any]]:
    """按分项（device_category / device_type）聚合统计。"""
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
        results.append({
            "sub_item": sub_item,
            "label": sub_item_labels.get(sub_item, sub_item),
            "total_consumption": round(value["consumption"], 3),
            "avg_load": round(value["load"], 3),
            "device_count": len(value["device_ids"]),
            "energy_categories": sorted(value["energy_categories"]),
        })
    return results


# ==================== 排行 ====================


def build_location_rankings(
    device_stats: Dict[int, Dict[str, Any]],
    device_by_id: Dict[int, Device],
    locations_by_id: Dict[int, Location],
    target_types: set[str],
    top_n: int,
    find_ancestor: Any,
) -> list[Dict[str, Any]]:
    """按位置（区域/楼栋）聚合并排行 Top N。

    find_ancestor 由调用方注入，签名为 (locations_by_id, location_id, target_types) -> Location | None
    （避免 domain 层依赖 services 包）。
    """
    aggregates: Dict[int, Dict[str, Any]] = defaultdict(
        lambda: {"consumption": 0.0, "load": 0.0, "energy_breakdown": defaultdict(float)}
    )
    for device_id, stats in device_stats.items():
        device = device_by_id.get(device_id)
        if not device or device.location_id is None:
            continue
        target = find_ancestor(locations_by_id, device.location_id, target_types)
        if target is None:
            continue
        item = aggregates[target.id]
        item["consumption"] += stats["total_consumption"]
        item["load"] += stats["avg_load"]
        item["energy_breakdown"][device.energy_type or stats["energy_type"]] += stats["total_consumption"]

    results = []
    for current_location_id, value in aggregates.items():
        location = locations_by_id.get(current_location_id)
        if not location:
            continue
        results.append({
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
        })
    results.sort(key=lambda item: item["total_consumption"], reverse=True)
    return results[:top_n]


def build_device_rankings(
    device_stats: Dict[int, Dict[str, Any]],
    device_by_id: Dict[int, Device],
    locations_by_id: Dict[int, Location],
    top_n: int,
) -> list[Dict[str, Any]]:
    """按设备消耗排行 Top N。"""
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
        items.append({
            "device_id": device.id,
            "name": device.name,
            "device_type": device.device_type,
            "device_category": device.device_category,
            "energy_type": device.energy_type or stats["energy_type"],
            "location": location_name,
            "total_consumption": round(stats["total_consumption"], 3),
            "avg_load": round(stats["avg_load"], 3),
        })
    items.sort(key=lambda item: item["total_consumption"], reverse=True)
    return items[:top_n]


# ==================== 异常识别 ====================


def build_anomaly_item(
    kind: str,
    severity: str,
    device: Device,
    locations_by_id: Dict[int, Location],
    message: str,
    detected_at: Optional[datetime],
) -> Dict[str, Any]:
    """构造单条异常事件项。"""
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


def build_anomaly_summary(
    health_rows: list[DeviceIngestionHealth],
    unresolved_alarm_rows: list[Alarm],
    device_by_id: Dict[int, Device],
    locations_by_id: Dict[int, Location],
    end_time: datetime,
    top_n: int,
) -> Dict[str, Any]:
    """聚合异常信号：数据断档、采集失败、活跃告警。"""
    items: list[Dict[str, Any]] = []
    data_gap_count = 0
    failure_count = 0

    for health in health_rows:
        device = device_by_id.get(health.device_id)
        if not device:
            continue
        if health.last_message_at is None:
            data_gap_count += 1
            items.append(build_anomaly_item(
                kind="data_gap",
                severity="critical",
                device=device,
                locations_by_id=locations_by_id,
                message="设备暂无接入报文，无法形成稳定分析走势。",
                detected_at=health.updated_at,
            ))
            continue

        if end_time - health.last_message_at > timedelta(hours=2):
            data_gap_count += 1
            items.append(build_anomaly_item(
                kind="data_gap",
                severity="warning",
                device=device,
                locations_by_id=locations_by_id,
                message=f"最近报文停留在 {health.last_message_at:%Y-%m-%d %H:%M}，存在数据断档风险。",
                detected_at=health.last_message_at,
            ))
        elif health.consecutive_failures >= 3:
            failure_count += 1
            items.append(build_anomaly_item(
                kind="ingestion_failure",
                severity="warning",
                device=device,
                locations_by_id=locations_by_id,
                message=health.last_failure_reason or "设备接入连续失败，需要排查采集链路。",
                detected_at=health.last_failure_at or health.updated_at,
            ))

    active_alarm_count = 0
    for alarm in unresolved_alarm_rows:
        device = device_by_id.get(alarm.device_id)
        if not device:
            continue
        active_alarm_count += 1
        items.append(build_anomaly_item(
            kind="active_alarm",
            severity=alarm.severity,
            device=device,
            locations_by_id=locations_by_id,
            message=alarm.message,
            detected_at=alarm.last_seen_at or alarm.timestamp,
        ))

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


# ==================== Scope / Summary / Insights ====================


def build_scope_summary(
    devices: list[Device],
    locations_by_id: Dict[int, Location],
    relevant_location_ids: set[int],
    site_location_types: set[str],
    location_id: Optional[int],
    energy_type: Optional[str],
) -> Dict[str, Any]:
    """构造 scope 区域/能源/分项汇总。"""
    location_counts = {
        "park": 0,
        "campus": 0,
        "site": 0,
        "area": 0,
        "zone": 0,
        "building": 0,
    }
    for current_location_id in relevant_location_ids:
        location = locations_by_id.get(current_location_id)
        if location and location.location_type in location_counts:
            location_counts[location.location_type] += 1

    return {
        "location_id": location_id,
        "location_type": resolve_scope_location_type(locations_by_id, location_id),
        "location_counts": location_counts,
        "campus_entity_count": sum(
            location_counts[key] for key in site_location_types if key in location_counts
        ),
        "energy_categories": sorted({
            device.energy_type
            for device in devices
            if device.energy_type and (energy_type is None or device.energy_type == energy_type)
        }),
        "sub_items": sorted({
            device.device_category or device.device_type
            for device in devices
            if device.device_category or device.device_type
        }),
    }


def build_summary(
    devices: list[Device],
    device_by_id: Dict[int, Device],
    device_stats: Dict[int, Dict[str, Any]],
    anomaly_summary: Dict[str, Any],
) -> Dict[str, Any]:
    """构造分析窗口顶层 summary。"""
    total_consumption = sum(item["total_consumption"] for item in device_stats.values())
    avg_load = sum(item["avg_load"] for item in device_stats.values())
    return {
        "total_consumption": round(total_consumption, 3),
        "avg_load": round(avg_load, 3),
        "device_count": len(devices),
        "active_device_count": sum(1 for device in devices if device.is_active),
        "covered_energy_type_count": len({
            (device_by_id.get(device_id).energy_type if device_by_id.get(device_id) else stats["energy_type"])
            for device_id, stats in device_stats.items()
        }),
        "covered_sub_item_count": len({
            device.device_category or device.device_type
            for device in devices
            if device.device_category or device.device_type
        }),
        "anomaly_count": anomaly_summary["total_count"],
        "consumption_stat_basis": "period_delta_from_cumulative_reading",
    }


def build_insights(
    comparison: Dict[str, Any],
    ranking: Dict[str, Any],
    anomaly: Dict[str, Any],
    summary: Dict[str, Any],
) -> list[Dict[str, Any]]:
    """根据对比、排行、异常生成洞察文案，最多 4 条。"""
    insights = []
    energy_categories = comparison.get("energy_categories", [])
    if energy_categories:
        dominant = energy_categories[0]
        insights.append({
            "title": f"{dominant['label']} 仍是当前主导能源",
            "detail": f"本周期 {dominant['label']} 累计占比 {dominant['ratio'] * 100:.1f}%，可优先用于趋势和节能动作跟踪。",
            "severity": "info",
            "dimension": "energy_type",
        })

    change_rate = comparison.get("period_over_period", {}).get("change_rate")
    if change_rate is not None:
        insights.append({
            "title": f"总能耗环比{'上升' if change_rate > 0 else '下降'}",
            "detail": f"当前周期较上一周期变化 {change_rate * 100:.1f}%，可结合区域和分项排行继续定位来源。",
            "severity": "warning" if change_rate > 0.1 else "info",
            "dimension": "comparison",
        })

    areas = ranking.get("areas") or []
    top_area = areas[0] if areas else None
    if top_area:
        insights.append({
            "title": f"{top_area['name']} 是当前高消耗区域",
            "detail": f"该区域累计消耗 {top_area['total_consumption']:.2f}，适合作为下一步区域级分析和巡检联动的优先对象。",
            "severity": "info",
            "dimension": "area",
        })

    if anomaly["summary"]["total_count"]:
        insights.append({
            "title": "当前存在待跟进异常信号",
            "detail": f"已识别 {anomaly['summary']['total_count']} 条运营异常信号，当前以接入断档和未恢复告警为主。",
            "severity": "warning",
            "dimension": "anomaly",
        })

    if not insights:
        insights.append({
            "title": "当前分析窗口暂无明显波动",
            "detail": f"已覆盖 {summary['device_count']} 台设备，可继续扩大真实采集覆盖后再提升对比和异常精度。",
            "severity": "info",
            "dimension": "summary",
        })
    return insights[:4]
