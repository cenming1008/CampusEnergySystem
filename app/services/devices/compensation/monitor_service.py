"""
补偿类设备监控聚合服务。

通用设备监控服务只负责组装页面总览；补偿设备族的子型分流、关键指标来源
和 SVG / 电容补偿控制器专属监控语义统一收敛在这里。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlmodel import Session, select

from app.core.settings import settings
from app.domain.compensation_rules import (
    build_capacitor_bank_circuit_summary,
    build_capacitor_bank_temperature_health,
    build_pq_reference_line,
    build_svg_monitor_payload_parts,
    clamp_health_score,
    comm_health_score,
    health_rating,
    max_defined_number,
    normalize_power_factor,
    optional_float,
    resolve_capacitor_bank_control_mode,
    resolve_capacitor_bank_control_log_mode,
    score_by_threshold,
    resolve_svg_control_mode,
    switching_health_score,
    voltage_stability_score,
)
from app.domain.device_payloads import resolve_compensation_subtype
from app.models.tables import CapacitorBankControlProfile, CapacitorBankTelemetry, Device, DeviceControlLog, SVGTelemetry
from app.repositories.device_repository import DeviceRepository
from app.services.devices.compensation.capacitor_bank.control_command_service import CapacitorBankControlCommandService
from app.services.devices.compensation.capacitor_bank.control_profile_service import CapacitorBankControlProfileService
from app.services.devices.compensation.capacitor_bank.service import CapacitorBankService
from app.services.devices.compensation.svg.service import SVGService


class CompensationMonitorService:
    """构建补偿类设备监控页专属 payload。"""

    _HEALTH_REALTIME_FRESH_THRESHOLD_SECONDS = 120
    _HEALTH_VOLTAGE_THD_THRESHOLD = 5.0
    _HEALTH_CURRENT_THD_THRESHOLD = 5.0
    _HEALTH_TEMP_THRESHOLD = 55.0
    _PQ_DEFAULT_P_MAX = 400.0
    _PQ_DEFAULT_Q_MAX = 200.0

    @staticmethod
    def _build_metric(value: Any, *, source: str, state: str) -> dict[str, Any]:
        return {
            "value": value,
            "source": source,
            "state": state,
        }

    @staticmethod
    def _is_realtime_fresh(timestamp: Any) -> bool:
        if timestamp is None:
            return False
        if not isinstance(timestamp, datetime):
            return False
        now = datetime.now(tz=timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
        delta = now - timestamp
        return 0 <= delta.total_seconds() <= CompensationMonitorService._HEALTH_REALTIME_FRESH_THRESHOLD_SECONDS

    def _build_capacitor_bank_health_model(
        telemetry: Optional[CapacitorBankTelemetry],
        realtime: dict[str, Any],
        runtime_status: Optional[dict[str, Any]],
        *,
        cabinet_temperature: Optional[float],
    ) -> dict[str, Any]:
        vthd = max_defined_number((
            getattr(telemetry, "voltage_thd_a", None),
            getattr(telemetry, "voltage_thd_b", None),
            getattr(telemetry, "voltage_thd_c", None),
        ))
        cthd = max_defined_number((
            getattr(telemetry, "current_harmonic_a", None),
            getattr(telemetry, "current_harmonic_b", None),
            getattr(telemetry, "current_harmonic_c", None),
        ))
        switching_flags = (
            getattr(telemetry, "overvoltage_alarm_a", None),
            getattr(telemetry, "overvoltage_alarm_b", None),
            getattr(telemetry, "overvoltage_alarm_c", None),
            getattr(telemetry, "undercurrent_a", None),
            getattr(telemetry, "undercurrent_b", None),
            getattr(telemetry, "undercurrent_c", None),
        )
        ingestion_status = (runtime_status or {}).get("ingestion_status")
        breakdown = [
            {
                "key": "comm",
                "label": "通讯链路",
                "value": comm_health_score(
                    ingestion_status,
                    CompensationMonitorService._is_realtime_fresh(realtime.get("timestamp")),
                ),
            },
            {
                "key": "voltageHarmonic",
                "label": "电压谐波",
                "value": score_by_threshold(
                    vthd,
                    CompensationMonitorService._HEALTH_VOLTAGE_THD_THRESHOLD,
                ),
            },
            {
                "key": "currentHarmonic",
                "label": "电流谐波",
                "value": score_by_threshold(
                    cthd,
                    CompensationMonitorService._HEALTH_CURRENT_THD_THRESHOLD,
                ),
            },
            {
                "key": "switching",
                "label": "投切动作",
                "value": switching_health_score(switching_flags),
            },
            {
                "key": "temperature",
                "label": "温度",
                "value": score_by_threshold(
                    float(cabinet_temperature) if cabinet_temperature is not None else None,
                    CompensationMonitorService._HEALTH_TEMP_THRESHOLD,
                ),
            },
            {
                "key": "voltageStability",
                "label": "电压稳定",
                "value": voltage_stability_score(realtime.get("voltage")),
            },
        ]
        defined_scores = [item["value"] for item in breakdown if item["value"] is not None]
        score = clamp_health_score(sum(defined_scores) / len(defined_scores))
        return {
            "score": score,
            **health_rating(score),
            "breakdown": breakdown,
        }

    @staticmethod
    def _build_capacitor_bank_pq_model(
        device: Device,
        realtime: dict[str, Any],
        profile: Optional[CapacitorBankControlProfile],
    ) -> dict[str, Any]:
        p = optional_float(realtime.get("flow_rate"))
        q = optional_float(realtime.get("reactive_power"))
        rated_capacity = optional_float(getattr(device, "rated_capacity", None)) or 0.0

        p_max = max(
            CompensationMonitorService._PQ_DEFAULT_P_MAX,
            rated_capacity,
            abs(p or 0.0) * 1.2,
        )
        q_max = max(
            CompensationMonitorService._PQ_DEFAULT_Q_MAX,
            rated_capacity * 0.5,
            abs(q or 0.0) * 1.2,
        )

        threshold_pf = normalize_power_factor(
            getattr(profile, "switch_on_power_factor", None) if profile else None,
        ) or 0.9
        target_pf = normalize_power_factor(
            getattr(profile, "switch_off_power_factor", None) if profile else None,
        ) or 0.95
        reference_lines = [
            build_pq_reference_line(threshold_pf, role="threshold"),
            build_pq_reference_line(target_pf, role="target"),
        ]

        return {
            "point": {
                "p": p,
                "q": q,
            },
            "axis": {
                "pMax": round(p_max, 1),
                "qMax": round(q_max, 1),
            },
            "referenceLines": reference_lines,
            "targetPowerFactor": round(target_pf, 3),
        }

    @staticmethod
    def _get_control_logs(session: Session, device_id: int, limit: int = 20) -> list[DeviceControlLog]:
        CapacitorBankControlCommandService.expire_pending_control_logs(session, device_id=device_id)
        return DeviceRepository.list_control_logs(session, device_id=device_id, limit=limit)

    @staticmethod
    def _get_latest_svg_telemetry(session: Session, device_id: int) -> Optional[SVGTelemetry]:
        return session.exec(
            select(SVGTelemetry)
            .where(SVGTelemetry.device_id == device_id)
            .order_by(SVGTelemetry.timestamp.desc())
            .limit(1)
        ).first()

    @staticmethod
    def _get_latest_capacitor_bank_telemetry(session: Session, device_id: int) -> Optional[CapacitorBankTelemetry]:
        return session.exec(
            select(CapacitorBankTelemetry)
            .where(CapacitorBankTelemetry.device_id == device_id)
            .order_by(CapacitorBankTelemetry.timestamp.desc())
            .limit(1)
        ).first()

    @staticmethod
    def _resolve_control_mode_from_log(record: Optional[DeviceControlLog]) -> str:
        if record is None:
            return ""
        return resolve_capacitor_bank_control_log_mode(
            normalized_result=CapacitorBankControlCommandService.normalize_control_result(record.result),
            action=record.action,
            reason=record.reason,
        )

    @staticmethod
    def _resolve_capacitor_bank_control_mode(
        telemetry: Optional[CapacitorBankTelemetry],
        profile: Optional[CapacitorBankControlProfile],
        control_logs: list[DeviceControlLog],
        *,
        is_device_active: bool,
    ) -> dict[str, str]:
        latest_log_mode = ""
        latest_log_created_at = None
        for log in control_logs:
            latest_log_mode = CompensationMonitorService._resolve_control_mode_from_log(log)
            if latest_log_mode:
                latest_log_created_at = getattr(log, "created_at", None)
                break

        return resolve_capacitor_bank_control_mode(
            telemetry_mode=getattr(telemetry, "control_mode", None),
            telemetry_timestamp=getattr(telemetry, "timestamp", None),
            profile_mode=getattr(profile, "control_mode", None),
            profile_scheme=getattr(profile, "terminal_assignment_scheme", None),
            profile_timestamp=getattr(profile, "snapshot_timestamp", None),
            latest_log_mode=latest_log_mode,
            latest_log_created_at=latest_log_created_at,
            is_device_active=is_device_active,
        )

    @staticmethod
    def _resolve_svg_control_mode(telemetry: Optional[SVGTelemetry]) -> dict[str, str]:
        return resolve_svg_control_mode(getattr(telemetry, "auto_mode", None))

    @staticmethod
    def _build_capacitor_bank_circuit_summary(
        telemetry: Optional[CapacitorBankTelemetry],
        profile: Optional[CapacitorBankControlProfile],
    ) -> dict[str, Any]:
        explicit_total_counts: tuple[Optional[int], ...] = () if profile is None else (
            profile.phase_a_circuit_total_count,
            profile.phase_b_circuit_total_count,
            profile.phase_c_circuit_total_count,
            profile.common_1_circuit_total_count,
            profile.common_2_circuit_total_count,
            profile.common_3_circuit_total_count,
        )
        configured_output_counts: tuple[Optional[int], ...] = () if profile is None else (
            profile.common_output_circuit_count,
            profile.split_output_circuit_count,
        )
        telemetry_bitmasks = (
            getattr(telemetry, "circuit_state_phase_a", None),
            getattr(telemetry, "circuit_state_phase_b", None),
            getattr(telemetry, "circuit_state_phase_c", None),
            getattr(telemetry, "circuit_state_common_1", None),
            getattr(telemetry, "circuit_state_common_2", None),
            getattr(telemetry, "circuit_state_common_3", None),
        )
        profile_running_values: tuple[Optional[int], ...] = () if profile is None else (
            profile.phase_a_circuit_running_count,
            profile.phase_b_circuit_running_count,
            profile.phase_c_circuit_running_count,
            profile.common_group_1_running_count,
            profile.common_group_2_running_count,
            profile.common_group_3_running_count,
        )

        return build_capacitor_bank_circuit_summary(
            telemetry_running_count=getattr(telemetry, "running_circuit_count", None),
            telemetry_bitmasks=telemetry_bitmasks,
            explicit_total_counts=explicit_total_counts,
            configured_output_counts=configured_output_counts,
            profile_running_count=getattr(profile, "running_circuit_count", None),
            profile_running_values=profile_running_values,
        )

    @staticmethod
    def _build_capacitor_bank_temperature_health(
        telemetry: Optional[CapacitorBankTelemetry],
        profile: Optional[CapacitorBankControlProfile],
        *,
        cabinet_temperature: Optional[float],
    ) -> dict[str, Any]:
        return build_capacitor_bank_temperature_health(
            temp_alarm=getattr(telemetry, "temp_alarm", None),
            threshold=getattr(profile, "temperature_upper_limit", None),
            cabinet_temperature=cabinet_temperature,
            warning_margin=settings.compensation_temperature_warning_margin_c,
        )

    @staticmethod
    def _build_capacitor_bank_monitor(
        session: Session,
        device: Device,
        realtime: dict[str, Any],
        runtime_status: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        telemetry = CompensationMonitorService._get_latest_capacitor_bank_telemetry(session, device.id)
        profile = CapacitorBankControlProfileService.get_control_profile(session, device.id)
        control_logs = CompensationMonitorService._get_control_logs(session, device.id, limit=20)
        control_mode = CompensationMonitorService._resolve_capacitor_bank_control_mode(
            telemetry,
            profile,
            control_logs,
            is_device_active=bool(device.is_active),
        )
        circuit_summary = CompensationMonitorService._build_capacitor_bank_circuit_summary(telemetry, profile)

        capacity_usage_source = "estimated"
        capacity_usage_state = "mock"
        capacity_usage_value: Optional[float] = None
        if circuit_summary["has_realtime_state"]:
            capacity_usage_value = round(
                min(100.0, max(0.0, (circuit_summary["running_count"] / max(1, circuit_summary["total_count"])) * 100.0)),
                1,
            )
            capacity_usage_source = circuit_summary["source"]
            capacity_usage_state = "live"
        else:
            rated_capacity = float(getattr(device, "rated_capacity", 0) or 0)
            reactive_power = realtime.get("reactive_power")
            if rated_capacity > 0 and reactive_power is not None:
                capacity_usage_value = round(
                    min(100.0, max(0.0, (abs(float(reactive_power)) / rated_capacity) * 100.0)),
                    1,
                )

        cabinet_temperature = getattr(telemetry, "temperature", None)
        cabinet_temperature_source = "telemetry" if cabinet_temperature is not None else "realtime"
        cabinet_temperature_state = "live" if cabinet_temperature is not None else "missing"
        if cabinet_temperature is None:
            cabinet_temperature = realtime.get("temperature")
            if cabinet_temperature is not None:
                cabinet_temperature_state = "live"
            else:
                cabinet_temperature_source = "missing"
        temperature_health = CompensationMonitorService._build_capacitor_bank_temperature_health(
            telemetry,
            profile,
            cabinet_temperature=cabinet_temperature,
        )

        profile_status = CapacitorBankControlProfileService.get_profile_source_status(profile)
        capabilities = CapacitorBankService.get_control_capabilities()

        return {
            "subtype": "capacitor_bank_controller",
            "control_mode": control_mode,
            "circuit_summary": circuit_summary,
            "health_model": CompensationMonitorService._build_capacitor_bank_health_model(
                telemetry,
                realtime,
                runtime_status,
                cabinet_temperature=cabinet_temperature,
            ),
            "pq_model": CompensationMonitorService._build_capacitor_bank_pq_model(device, realtime, profile),
            "profile_status": {
                "source_status": profile_status,
                "is_stale": profile_status == "stale",
            },
            "key_metrics": {
                "capacity_utilization": CompensationMonitorService._build_metric(
                    capacity_usage_value,
                    source=capacity_usage_source,
                    state=capacity_usage_state if capacity_usage_value is not None else "missing",
                ),
                "cabinet_temperature": CompensationMonitorService._build_metric(
                    cabinet_temperature,
                    source=cabinet_temperature_source,
                    state=cabinet_temperature_state,
                ),
                "temperature_health": temperature_health,
                "compensation_level": CompensationMonitorService._build_metric(
                    circuit_summary["running_count"],
                    source=circuit_summary["source"],
                    state=circuit_summary["state"],
                ),
            },
            "capabilities_summary": {
                "supports_read": bool(capabilities.get("supports_read")),
                "supports_write": bool(capabilities.get("supports_write")),
                "supports_remote_control": bool(capabilities.get("supports_remote_control")),
            },
            "status_tags": [],
        }

    @staticmethod
    def _build_svg_monitor(
        session: Session,
        device: Device,
        realtime: dict[str, Any],
    ) -> dict[str, Any]:
        telemetry = CompensationMonitorService._get_latest_svg_telemetry(session, device.id)
        profile = SVGService.get_operations_profile(session, device.id)
        control_mode = CompensationMonitorService._resolve_svg_control_mode(telemetry)
        svg_payload_parts = build_svg_monitor_payload_parts(
            capacity_utilization=getattr(telemetry, "capacity_utilization", None),
            profile_module_count=getattr(profile, "module_count", 0),
            rated_capacity=getattr(device, "rated_capacity", None),
            reactive_power=realtime.get("reactive_power"),
            cabinet_temperature=getattr(telemetry, "cabinet_temp", None),
            realtime_temperature=realtime.get("temperature"),
        )

        return {
            "subtype": "svg",
            "control_mode": control_mode,
            "circuit_summary": svg_payload_parts["circuit_summary"],
            "profile_status": None,
            "key_metrics": {
                "capacity_utilization": svg_payload_parts["capacity_utilization_metric"],
                "cabinet_temperature": svg_payload_parts["cabinet_temperature_metric"],
                "compensation_level": svg_payload_parts["compensation_level_metric"],
            },
            "capabilities_summary": SVGService.get_control_capabilities(),
            "status_tags": [],
        }

    @staticmethod
    def build_monitor(
        session: Session,
        device: Device,
        realtime: dict[str, Any],
        runtime_status: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        subtype = resolve_compensation_subtype(
            getattr(device, "device_type", None),
            getattr(device, "device_subtype", None),
        )
        if subtype == "capacitor_bank_controller":
            return CompensationMonitorService._build_capacitor_bank_monitor(session, device, realtime, runtime_status)
        if subtype == "svg":
            return CompensationMonitorService._build_svg_monitor(session, device, realtime)
        return None
