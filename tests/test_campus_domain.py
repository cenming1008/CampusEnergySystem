from dataclasses import dataclass
from datetime import datetime
from types import SimpleNamespace

from app.domain.campus_rules import (
    build_alarm_summary,
    build_energy_category_summary,
    build_location_rankings,
    build_realtime_load_trend,
    build_subitem_statistics,
)


@dataclass
class Summary:
    energy_type: str
    total_consumption: float
    load_sum: float
    load_count: int
    device_id: int = 0


def test_build_energy_category_summary_sorts_and_preserves_response_shape():
    summaries = [
        Summary("water", 12.3456, 3.0, 0),
        Summary("electricity", 30.1111, 15.0, 3),
        Summary("electricity", 5.0, 2.0, 1),
    ]

    result = build_energy_category_summary(summaries)

    assert result == [
        {
            "energy_category": "electricity",
            "label": "电",
            "total_consumption": 35.111,
            "avg_load": 4.25,
            "ratio": 0.7399,
            "estimated_carbon": 27.562,
        },
        {
            "energy_category": "water",
            "label": "水",
            "total_consumption": 12.346,
            "avg_load": 3.0,
            "ratio": 0.2602,
            "estimated_carbon": 0.0,
        },
    ]


def test_build_subitem_statistics_groups_by_device_category_and_ignores_missing_devices():
    summaries = [
        Summary("electricity", 20.555, 6.0, 2, device_id=1),
        Summary("water", 4.0, 2.0, 0, device_id=1),
        Summary("gas", 10.0, 3.0, 1, device_id=2),
        Summary("electricity", 100.0, 100.0, 1, device_id=99),
    ]
    device_by_id = {
        1: SimpleNamespace(id=1, device_category="load", device_type="meter"),
        2: SimpleNamespace(id=2, device_category=None, device_type="gas_meter"),
    }

    result = build_subitem_statistics(summaries, device_by_id)

    assert result == [
        {
            "sub_item": "load",
            "label": "动力/普通负荷",
            "total_consumption": 24.555,
            "avg_load": 4.0,
            "device_count": 1,
            "energy_categories": ["electricity", "water"],
        },
        {
            "sub_item": "gas_meter",
            "label": "燃气计量",
            "total_consumption": 10.0,
            "avg_load": 3.0,
            "device_count": 1,
            "energy_categories": ["gas"],
        },
    ]


def test_build_realtime_load_trend_groups_rows_and_ignores_negative_deltas():
    t1 = datetime(2026, 6, 2, 8, 0, 0)
    t2 = datetime(2026, 6, 2, 8, 15, 0)
    t3 = datetime(2026, 6, 2, 8, 30, 0)
    rows = [
        SimpleNamespace(device_id=1, energy_type="electricity", timestamp=t2, flow_rate=3.3333, consumption=12.5),
        SimpleNamespace(device_id=1, energy_type="electricity", timestamp=t1, flow_rate=2.0, consumption=10.0),
        SimpleNamespace(device_id=2, energy_type="water", timestamp=t2, flow_rate=None, consumption=4.0),
        SimpleNamespace(device_id=2, energy_type="water", timestamp=t3, flow_rate=1.25, consumption=2.0),
    ]

    result = build_realtime_load_trend(rows)

    assert result == [
        {"timestamp": t1, "total_load": 2.0, "total_consumption": 0.0},
        {"timestamp": t2, "total_load": 3.333, "total_consumption": 2.5},
        {"timestamp": t3, "total_load": 1.25, "total_consumption": 0.0},
    ]


def test_build_location_rankings_rolls_summaries_up_to_target_locations():
    locations_by_id = {
        1: SimpleNamespace(id=1, name="North Area", location_type="area", full_path="Campus/North", parent_id=None),
        2: SimpleNamespace(id=2, name="South Area", location_type="area", full_path="Campus/South", parent_id=None),
        10: SimpleNamespace(id=10, name="Lab A", location_type="building", full_path="Campus/North/Lab A", parent_id=1),
    }
    device_by_id = {
        101: SimpleNamespace(id=101, location_id=10),
        102: SimpleNamespace(id=102, location_id=2),
        103: SimpleNamespace(id=103, location_id=None),
    }
    summaries = [
        Summary("electricity", 18.1234, 6.0, 2, device_id=101),
        Summary("water", 4.0, 2.0, 0, device_id=101),
        Summary("gas", 30.0, 5.0, 1, device_id=102),
        Summary("electricity", 99.0, 99.0, 1, device_id=103),
    ]

    def find_ancestor(locations, location_id, target_types):
        current_id = location_id
        while current_id is not None:
            location = locations.get(current_id)
            if not location:
                return None
            if location.location_type in target_types:
                return location
            current_id = location.parent_id
        return None

    result = build_location_rankings(
        summaries,
        device_by_id,
        locations_by_id,
        {"area"},
        top_n=1,
        find_ancestor=find_ancestor,
    )

    assert result == [
        {
            "location_id": 2,
            "name": "South Area",
            "location_type": "area",
            "full_path": "Campus/South",
            "total_consumption": 30.0,
            "avg_load": 5.0,
            "energy_breakdown": {"gas": 30.0},
        }
    ]


def test_build_alarm_summary_counts_status_severity_locations_and_latest():
    t1 = datetime(2026, 6, 2, 9, 0, 0)
    t2 = datetime(2026, 6, 2, 9, 5, 0)
    t3 = datetime(2026, 6, 2, 9, 10, 0)
    locations_by_id = {
        1: SimpleNamespace(id=1, name="North Area", location_type="area", full_path="Campus/North", parent_id=None),
        2: SimpleNamespace(id=2, name="Lab A", location_type="building", full_path="Campus/North/Lab A", parent_id=1),
    }
    device_by_id = {
        101: SimpleNamespace(id=101, location_id=2),
        102: SimpleNamespace(id=102, location_id=None),
    }
    alarms = [
        SimpleNamespace(
            id=1,
            device_id=101,
            message="High load",
            severity="warning",
            category="energy",
            timestamp=t1,
            is_resolved=False,
        ),
        SimpleNamespace(
            id=2,
            device_id=101,
            message="Meter offline",
            severity="critical",
            category="device",
            timestamp=t2,
            is_resolved=True,
        ),
        SimpleNamespace(
            id=3,
            device_id=102,
            message="No location",
            severity="warning",
            category="device",
            timestamp=t3,
            is_resolved=False,
        ),
    ]

    def find_ancestor(locations, location_id, target_types):
        current_id = location_id
        while current_id is not None:
            location = locations.get(current_id)
            if not location:
                return None
            if location.location_type in target_types:
                return location
            current_id = location.parent_id
        return None

    result = build_alarm_summary(
        alarms,
        device_by_id,
        locations_by_id,
        {"area", "building"},
        find_ancestor=find_ancestor,
    )

    assert result == {
        "total_count": 3,
        "unresolved_count": 2,
        "resolved_count": 1,
        "by_severity": {"critical": 1, "warning": 2},
        "top_locations": [
            {"location_id": 2, "name": "Lab A", "location_type": "building", "alarm_count": 2},
        ],
        "latest": [
            {
                "id": 1,
                "device_id": 101,
                "message": "High load",
                "severity": "warning",
                "category": "energy",
                "timestamp": t1,
                "is_resolved": False,
            },
            {
                "id": 2,
                "device_id": 101,
                "message": "Meter offline",
                "severity": "critical",
                "category": "device",
                "timestamp": t2,
                "is_resolved": True,
            },
            {
                "id": 3,
                "device_id": 102,
                "message": "No location",
                "severity": "warning",
                "category": "device",
                "timestamp": t3,
                "is_resolved": False,
            },
        ],
    }
