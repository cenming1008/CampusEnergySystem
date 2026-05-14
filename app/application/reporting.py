"""
报表导出用例。
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

from sqlmodel import Session

from app.core.access_control import get_allowed_device_ids
from app.domain.device_payloads import describe_device_type_semantics
from app.models.tables import User
from app.services.energy_service import EnergyService
from app.services.report_service import ReportService


@dataclass
class CsvExportPayload:
    filename: str
    content: str


@dataclass(frozen=True)
class DeviceHistoryField:
    key: str
    label: str
    group_key: str
    group_label: str
    accessor: Callable[[Any, Any], Any]
    default: bool = False
    required: bool = False


REPORT_DEFINITIONS = {
    "energy_detail": {
        "headers": ["时间", "设备ID", "设备名称", "能源类型", "电压(V)", "电流(A)", "功率/流量", "累计消耗", "设备类型", "设备类别", "对象语义", "点位语义"],
        "rows_loader": "energy",
    },
    "alarm_history": {
        "headers": ["时间", "设备ID", "设备名称", "严重级别", "是否已恢复", "消息", "恢复人", "恢复时间"],
        "rows_loader": "alarm",
    },
    "carbon_emission": {
        "headers": ["时间", "设备ID", "设备名称", "能源类型", "能耗", "碳排放", "设备类型", "设备类别", "对象语义", "点位语义"],
        "rows_loader": "carbon",
    },
    "multi_energy_summary": {
        "headers": ["能源类型", "周期消耗", "累计单位", "平均瞬时值", "瞬时单位", "峰值瞬时值", "样本数", "碳排估算(kg CO2)", "碳排边界"],
        "rows_loader": "multi_energy_summary",
    },
    "device_history": {
        "headers": [],
        "rows_loader": "device_history",
    },
}

GENERIC_DEVICE_HISTORY_HEADERS = ["时间", "设备ID", "设备名称", "能源类型", "电压(V)", "电流(A)", "功率/流量", "累计消耗", "设备类型", "设备类别"]

CAPACITOR_BANK_HISTORY_HEADERS = [
    "时间",
    "设备ID",
    "设备名称",
    "设备类型",
    "A相电压(V)",
    "B相电压(V)",
    "C相电压(V)",
    "A相电流(A)",
    "B相电流(A)",
    "C相电流(A)",
    "A相功率因数",
    "B相功率因数",
    "C相功率因数",
    "A相有功(kW)",
    "B相有功(kW)",
    "C相有功(kW)",
    "A相无功(kvar)",
    "B相无功(kvar)",
    "C相无功(kvar)",
    "A相视在(kVA)",
    "B相视在(kVA)",
    "C相视在(kVA)",
    "A相电压THD(%)",
    "B相电压THD(%)",
    "C相电压THD(%)",
    "A相谐波电流(A)",
    "B相谐波电流(A)",
    "C相谐波电流(A)",
    "频率(Hz)",
    "柜内温度(°C)",
    "分补投入回路数",
    "公补投入回路数",
    "当前投入回路总数",
    "控制模式",
    "最近自动动作",
]


def _row_attr(row, key: str):
    return getattr(row, key, "")


def _device_attr(device, key: str):
    return getattr(device, key, "")


GENERIC_DEVICE_HISTORY_FIELDS = [
    DeviceHistoryField("timestamp", "时间", "required", "必导字段", lambda device, row: row.timestamp.strftime("%Y-%m-%d %H:%M:%S"), required=True),
    DeviceHistoryField("device_id", "设备ID", "base", "基础信息", lambda device, row: row.device_id, default=True),
    DeviceHistoryField("device_name", "设备名称", "base", "基础信息", lambda device, row: _device_attr(device, "name"), default=True),
    DeviceHistoryField("energy_type", "能源类型", "telemetry", "通用遥测", lambda device, row: _row_attr(row, "energy_type"), default=True),
    DeviceHistoryField("voltage", "电压(V)", "telemetry", "通用遥测", lambda device, row: _row_attr(row, "voltage"), default=True),
    DeviceHistoryField("current", "电流(A)", "telemetry", "通用遥测", lambda device, row: _row_attr(row, "current"), default=True),
    DeviceHistoryField("flow_rate", "功率/流量", "telemetry", "通用遥测", lambda device, row: _row_attr(row, "flow_rate"), default=True),
    DeviceHistoryField("consumption", "累计消耗", "telemetry", "通用遥测", lambda device, row: _row_attr(row, "consumption"), default=True),
    DeviceHistoryField("device_type", "设备类型", "semantics", "设备语义", lambda device, row: _device_attr(device, "device_type")),
    DeviceHistoryField("device_category", "设备类别", "semantics", "设备语义", lambda device, row: _device_attr(device, "device_category")),
]


CAPACITOR_BANK_DEVICE_HISTORY_FIELDS = [
    DeviceHistoryField("timestamp", "时间", "required", "必导字段", lambda device, row: row.timestamp.strftime("%Y-%m-%d %H:%M:%S"), required=True),
    DeviceHistoryField("device_id", "设备ID", "base", "基础信息", lambda device, row: row.device_id),
    DeviceHistoryField("device_name", "设备名称", "base", "基础信息", lambda device, row: _device_attr(device, "name"), default=True),
    DeviceHistoryField("voltage_a", "A相电压(V)", "three_phase", "三相电参", lambda device, row: _row_attr(row, "voltage_a")),
    DeviceHistoryField("voltage_b", "B相电压(V)", "three_phase", "三相电参", lambda device, row: _row_attr(row, "voltage_b")),
    DeviceHistoryField("voltage_c", "C相电压(V)", "three_phase", "三相电参", lambda device, row: _row_attr(row, "voltage_c")),
    DeviceHistoryField("current_a", "A相电流(A)", "three_phase", "三相电参", lambda device, row: _row_attr(row, "current_a")),
    DeviceHistoryField("current_b", "B相电流(A)", "three_phase", "三相电参", lambda device, row: _row_attr(row, "current_b")),
    DeviceHistoryField("current_c", "C相电流(A)", "three_phase", "三相电参", lambda device, row: _row_attr(row, "current_c")),
    DeviceHistoryField("reactive_power_a", "A相无功(kvar)", "compensation_effect", "补偿效果", lambda device, row: _row_attr(row, "reactive_power_a"), default=True),
    DeviceHistoryField("reactive_power_b", "B相无功(kvar)", "compensation_effect", "补偿效果", lambda device, row: _row_attr(row, "reactive_power_b"), default=True),
    DeviceHistoryField("reactive_power_c", "C相无功(kvar)", "compensation_effect", "补偿效果", lambda device, row: _row_attr(row, "reactive_power_c"), default=True),
    DeviceHistoryField("power_factor_a", "A相功率因数", "compensation_effect", "补偿效果", lambda device, row: _row_attr(row, "power_factor_a"), default=True),
    DeviceHistoryField("power_factor_b", "B相功率因数", "compensation_effect", "补偿效果", lambda device, row: _row_attr(row, "power_factor_b"), default=True),
    DeviceHistoryField("power_factor_c", "C相功率因数", "compensation_effect", "补偿效果", lambda device, row: _row_attr(row, "power_factor_c"), default=True),
    DeviceHistoryField("active_power_a", "A相有功(kW)", "compensation_effect", "补偿效果", lambda device, row: _row_attr(row, "active_power_a")),
    DeviceHistoryField("active_power_b", "B相有功(kW)", "compensation_effect", "补偿效果", lambda device, row: _row_attr(row, "active_power_b")),
    DeviceHistoryField("active_power_c", "C相有功(kW)", "compensation_effect", "补偿效果", lambda device, row: _row_attr(row, "active_power_c")),
    DeviceHistoryField("apparent_power_a", "A相视在(kVA)", "compensation_effect", "补偿效果", lambda device, row: _row_attr(row, "apparent_power_a")),
    DeviceHistoryField("apparent_power_b", "B相视在(kVA)", "compensation_effect", "补偿效果", lambda device, row: _row_attr(row, "apparent_power_b")),
    DeviceHistoryField("apparent_power_c", "C相视在(kVA)", "compensation_effect", "补偿效果", lambda device, row: _row_attr(row, "apparent_power_c")),
    DeviceHistoryField("voltage_thd_a", "A相电压THD(%)", "harmonic", "谐波", lambda device, row: _row_attr(row, "voltage_thd_a")),
    DeviceHistoryField("voltage_thd_b", "B相电压THD(%)", "harmonic", "谐波", lambda device, row: _row_attr(row, "voltage_thd_b")),
    DeviceHistoryField("voltage_thd_c", "C相电压THD(%)", "harmonic", "谐波", lambda device, row: _row_attr(row, "voltage_thd_c")),
    DeviceHistoryField("current_harmonic_a", "A相谐波电流(A)", "harmonic", "谐波", lambda device, row: _row_attr(row, "current_harmonic_a")),
    DeviceHistoryField("current_harmonic_b", "B相谐波电流(A)", "harmonic", "谐波", lambda device, row: _row_attr(row, "current_harmonic_b")),
    DeviceHistoryField("current_harmonic_c", "C相谐波电流(A)", "harmonic", "谐波", lambda device, row: _row_attr(row, "current_harmonic_c")),
    DeviceHistoryField("split_circuit_running_count", "分补投入回路数", "switching", "投切状态", lambda device, row: _row_attr(row, "split_circuit_running_count")),
    DeviceHistoryField("common_circuit_running_count", "公补投入回路数", "switching", "投切状态", lambda device, row: _row_attr(row, "common_circuit_running_count")),
    DeviceHistoryField("running_circuit_count", "当前投入回路总数", "switching", "投切状态", lambda device, row: _row_attr(row, "running_circuit_count"), default=True),
    DeviceHistoryField("frequency", "频率(Hz)", "runtime", "运行状态", lambda device, row: _row_attr(row, "frequency")),
    DeviceHistoryField("temperature", "柜内温度(°C)", "runtime", "运行状态", lambda device, row: _row_attr(row, "temperature"), default=True),
    DeviceHistoryField("control_mode", "控制模式", "runtime", "运行状态", lambda device, row: _row_attr(row, "control_mode"), default=True),
    DeviceHistoryField("last_auto_action", "最近自动动作", "runtime", "运行状态", lambda device, row: _row_attr(row, "last_auto_action")),
]


DEVICE_HISTORY_TEMPLATES = {
    "generic_energy": GENERIC_DEVICE_HISTORY_FIELDS,
    "capacitor_bank_controller": CAPACITOR_BANK_DEVICE_HISTORY_FIELDS,
}


def _safe_filename_date(value: Optional[datetime]) -> str:
    return value.strftime("%Y%m%d") if value else datetime.now().strftime("%Y%m%d")


def list_energy_report_rows_use_case(
    session: Session,
    current_user: Optional[User] = None,
    device_id: Optional[int] = None,
    energy_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
):
    """统一报表导出数据读取入口。"""
    return ReportService.list_energy_report_rows(
        session=session,
        current_user=current_user,
        device_id=device_id,
        energy_type=energy_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


def list_alarm_report_rows_use_case(
    session: Session,
    current_user: Optional[User] = None,
    device_id: Optional[int] = None,
    resolved: Optional[bool] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
) -> list[tuple[Alarm, Optional[str]]]:
    return ReportService.list_alarm_report_rows(
        session=session,
        current_user=current_user,
        device_id=device_id,
        resolved=resolved,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


def list_carbon_report_rows_use_case(
    session: Session,
    current_user: Optional[User] = None,
    device_id: Optional[int] = None,
    energy_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
) -> list[tuple[CarbonEmission, Optional[str]]]:
    return ReportService.list_carbon_report_rows(
        session=session,
        current_user=current_user,
        device_id=device_id,
        energy_type=energy_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


def build_multi_energy_summary_rows_use_case(
    session: Session,
    current_user: Optional[User] = None,
    device_id: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    if start_time is None or end_time is None:
        raise ValueError("multi_energy_summary 需要同时提供 start_time 和 end_time")

    energy_types = [item["energy_type"] for item in EnergyService.list_energy_type_catalog()]
    allowed_device_ids = get_allowed_device_ids(session, current_user)
    statistics = EnergyService.get_statistics_by_type(
        session=session,
        start_time=start_time,
        end_time=end_time,
        energy_types=energy_types,
        device_id=device_id,
        allowed_device_ids=allowed_device_ids,
    )
    carbon_summary = EnergyService.get_carbon_summary(
        session=session,
        start_time=start_time,
        end_time=end_time,
        device_id=device_id,
        allowed_device_ids=allowed_device_ids,
    )

    rows = []
    for energy_type in energy_types:
        stats = statistics.get(energy_type, {})
        if not stats or not stats.get("data_count"):
            continue
        semantics = EnergyService.get_energy_semantics(energy_type)
        carbon_payload = carbon_summary["by_energy_type"].get(energy_type, {})
        rows.append(
            {
                "energy_type": energy_type,
                "energy_label": semantics["label"],
                "total_consumption": stats["total_consumption"],
                "consumption_unit": stats["consumption_unit"],
                "avg_flow_rate": round(stats["avg_flow_rate"], 4),
                "flow_unit": stats["flow_unit"],
                "peak_flow_rate": round(stats["peak_flow_rate"], 4),
                "data_count": stats["data_count"],
                "carbon_emission": carbon_payload.get("carbon_emission", 0.0),
                "carbon_boundary": carbon_payload.get("boundary", carbon_summary.get("boundary", "display_estimate")),
            }
        )
    return rows


def list_device_history_report_rows_use_case(
    session: Session,
    current_user: Optional[User],
    device_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
) -> dict:
    return ReportService.list_device_history_report_rows(
        session=session,
        current_user=current_user,
        device_id=device_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


def _resolve_device_history_template_key(device) -> str:
    if getattr(device, "device_subtype", None) == "capacitor_bank_controller":
        return "capacitor_bank_controller"
    return "generic_energy"


def _device_history_fields_for_device(device) -> list[DeviceHistoryField]:
    return DEVICE_HISTORY_TEMPLATES[_resolve_device_history_template_key(device)]


def _field_config_payload(device) -> dict:
    fields = _device_history_fields_for_device(device)
    default_fields = [field.key for field in fields if field.default and not field.required]
    required_fields = [field.key for field in fields if field.required]
    groups_by_key: dict[str, dict] = {}
    for field in fields:
        if field.required:
            continue
        group = groups_by_key.setdefault(
            field.group_key,
            {"key": field.group_key, "label": field.group_label, "fields": []},
        )
        group["fields"].append({
            "key": field.key,
            "label": field.label,
            "default": field.default,
        })
    return {
        "device_id": getattr(device, "id", None),
        "template": _resolve_device_history_template_key(device),
        "required_fields": required_fields,
        "default_fields": default_fields,
        "groups": list(groups_by_key.values()),
    }


def build_device_history_field_config_use_case(
    session: Session,
    current_user: Optional[User],
    device_id: int,
) -> dict:
    device = ReportService.get_device_for_history_report(session, current_user, device_id)
    return _field_config_payload(device)


def _parse_requested_device_history_fields(fields: Optional[str]) -> list[str] | None:
    if fields is None:
        return None
    parsed = [field.strip() for field in fields.split(",") if field.strip()]
    return parsed or None


def _select_device_history_fields(device, fields: Optional[str]) -> list[DeviceHistoryField]:
    template_fields = _device_history_fields_for_device(device)
    field_by_key = {field.key: field for field in template_fields}
    required_keys = [field.key for field in template_fields if field.required]
    requested_keys = _parse_requested_device_history_fields(fields)
    if requested_keys is None:
        selected_keys = required_keys + [
            field.key for field in template_fields if field.default and not field.required
        ]
    else:
        invalid_keys = [key for key in requested_keys if key not in field_by_key]
        if invalid_keys:
            raise ValueError(f"不支持的导出字段: {', '.join(invalid_keys)}")
        selected_keys = required_keys + [key for key in requested_keys if key not in required_keys]

    selected_key_set = set(selected_keys)
    return [field for field in template_fields if field.key in selected_key_set]


def _write_device_history_rows(
    writer: csv.writer,
    device,
    rows,
    fields: Optional[str],
) -> None:
    selected_fields = _select_device_history_fields(device, fields)
    writer.writerow([field.label for field in selected_fields])
    for row in rows:
        writer.writerow([field.accessor(device, row) for field in selected_fields])


def build_report_csv_export_use_case(
    session: Session,
    current_user: Optional[User],
    report_type: str,
    device_id: Optional[int] = None,
    energy_type: Optional[str] = None,
    resolved: Optional[bool] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000,
    fields: Optional[str] = None,
) -> CsvExportPayload:
    normalized_report_type = report_type.strip().lower()
    report_definition = REPORT_DEFINITIONS.get(normalized_report_type)
    if report_definition is None:
        raise ValueError(f"不支持的报表类型: {report_type}")

    output = io.StringIO()
    writer = csv.writer(output)
    if report_definition["rows_loader"] == "energy":
        writer.writerow(report_definition["headers"])
        rows = list_energy_report_rows_use_case(
            session=session,
            current_user=current_user,
            device_id=device_id,
            energy_type=energy_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        for data, device_name, device_type, device_category in rows:
            semantics = describe_device_type_semantics(device_type)
            writer.writerow([
                data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                data.device_id,
                device_name,
                data.energy_type,
                data.voltage,
                data.current,
                data.flow_rate,
                data.consumption,
                device_type,
                device_category,
                semantics["object_role"],
                semantics["point_kind"],
            ])
    elif report_definition["rows_loader"] == "alarm":
        writer.writerow(report_definition["headers"])
        rows = list_alarm_report_rows_use_case(
            session=session,
            current_user=current_user,
            device_id=device_id,
            resolved=resolved,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        for alarm, device_name in rows:
            writer.writerow([
                alarm.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                alarm.device_id,
                device_name,
                alarm.severity,
                "是" if alarm.is_resolved else "否",
                alarm.message,
                alarm.resolved_by or "",
                alarm.resolved_at.strftime("%Y-%m-%d %H:%M:%S") if alarm.resolved_at else "",
            ])
    elif report_definition["rows_loader"] == "carbon":
        writer.writerow(report_definition["headers"])
        rows = list_carbon_report_rows_use_case(
            session=session,
            current_user=current_user,
            device_id=device_id,
            energy_type=energy_type,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        for data, device_name, device_type, device_category in rows:
            semantics = describe_device_type_semantics(device_type)
            writer.writerow([
                data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                data.device_id,
                device_name,
                data.energy_type,
                data.energy_consumption,
                data.carbon_emission,
                device_type,
                device_category,
                semantics["object_role"],
                semantics["point_kind"],
            ])
    elif report_definition["rows_loader"] == "multi_energy_summary":
        writer.writerow(report_definition["headers"])
        rows = build_multi_energy_summary_rows_use_case(
            session=session,
            current_user=current_user,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
        )
        for row in rows:
            writer.writerow([
                row["energy_label"],
                row["total_consumption"],
                row["consumption_unit"],
                row["avg_flow_rate"],
                row["flow_unit"],
                row["peak_flow_rate"],
                row["data_count"],
                row["carbon_emission"],
                row["carbon_boundary"],
            ])
    else:
        if device_id is None:
            raise ValueError("device_history 需要提供 device_id")
        payload = list_device_history_report_rows_use_case(
            session=session,
            current_user=current_user,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        device = payload["device"]
        _write_device_history_rows(writer, device, payload["rows"], fields)

    filename_prefix = normalized_report_type
    if normalized_report_type == "device_history" and device_id is not None:
        filename_prefix = f"device_history_{device_id}"
    return CsvExportPayload(
        filename=f"{filename_prefix}_{_safe_filename_date(end_time or start_time)}.csv",
        content=output.getvalue(),
    )
