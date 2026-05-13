"""
补偿类设备监控聚合服务。

通用设备监控服务只负责组装页面总览；补偿设备族的子型分流、关键指标来源
和 SVG / 电容补偿控制器专属监控语义统一收敛在这里。
"""

from __future__ import annotations

from typing import Any, Optional

from sqlmodel import Session, select

from app.core.settings import settings
from app.domain.device_payloads import resolve_compensation_subtype
from app.models.tables import CapacitorBankControlProfile, CapacitorBankTelemetry, Device, DeviceControlLog, SVGTelemetry
from app.repositories.device_repository import DeviceRepository
from app.services.devices.compensation.capacitor_bank.control_command_service import CapacitorBankControlCommandService
from app.services.devices.compensation.capacitor_bank.control_profile_service import CapacitorBankControlProfileService
from app.services.devices.compensation.capacitor_bank.service import CapacitorBankService
from app.services.devices.compensation.svg.service import SVGService


class CompensationMonitorService:
    """构建补偿类设备监控页专属 payload。"""

    @staticmethod
    def _build_metric(value: Any, *, source: str, state: str) -> dict[str, Any]:
        return {
            "value": value,
            "source": source,
            "state": state,
        }

    @staticmethod
    def _count_active_bits(value: Optional[int]) -> int:
        if not isinstance(value, int):
            return 0
        count = 0
        for bit in range(16):
            if value & (1 << bit):
                count += 1
        return count

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
        if CapacitorBankControlCommandService.normalize_control_result(record.result) != "success":
            return ""
        if record.action not in {"switch_control_mode", "manual_switch"}:
            return ""
        reason = (record.reason or "").strip()
        if "控制模式切换" not in reason:
            return ""
        if "手动模式" in reason:
            return "手动"
        if "自动模式" in reason:
            return "自动"
        return ""

    @staticmethod
    def _resolve_capacitor_bank_control_mode(
        telemetry: Optional[CapacitorBankTelemetry],
        profile: Optional[CapacitorBankControlProfile],
        control_logs: list[DeviceControlLog],
        *,
        is_device_active: bool,
    ) -> dict[str, str]:
        telemetry_mode = str(getattr(telemetry, "control_mode", "") or "").strip().lower()
        if telemetry_mode == "manual":
            return {"value": "手动", "source": "telemetry", "state": "live"}
        if telemetry_mode == "auto":
            return {"value": "自动", "source": "telemetry", "state": "live"}

        profile_mode = str(getattr(profile, "control_mode", "") or "").strip().lower()
        if profile_mode in {"manual", "手动"}:
            return {"value": "手动", "source": "profile", "state": "live"}
        if profile_mode in {"auto", "自动"}:
            return {"value": "自动", "source": "profile", "state": "live"}

        scheme = (getattr(profile, "terminal_assignment_scheme", None) or "").strip()
        if "手动" in scheme:
            return {"value": "手动", "source": "profile", "state": "live"}
        if "自动" in scheme:
            return {"value": "自动", "source": "profile", "state": "live"}

        for log in control_logs:
            log_mode = CompensationMonitorService._resolve_control_mode_from_log(log)
            if log_mode:
                return {"value": log_mode, "source": "control_log", "state": "live"}

        return {
            "value": "自动" if is_device_active else "待确认",
            "source": "placeholder",
            "state": "mock",
        }

    @staticmethod
    def _resolve_svg_control_mode(telemetry: Optional[SVGTelemetry]) -> dict[str, str]:
        auto_mode = getattr(telemetry, "auto_mode", None)
        if auto_mode is True:
            return {"value": "自动", "source": "telemetry", "state": "live"}
        if auto_mode is False:
            return {"value": "手动", "source": "telemetry", "state": "live"}
        return {"value": "待确认", "source": "placeholder", "state": "mock"}

    @staticmethod
    def _get_configured_capacitor_bank_circuit_total(profile: Optional[CapacitorBankControlProfile]) -> int:
        if profile is None:
            return 24
        explicit_counts: tuple[Optional[int], ...] = (
            profile.phase_a_circuit_total_count,
            profile.phase_b_circuit_total_count,
            profile.phase_c_circuit_total_count,
            profile.common_1_circuit_total_count,
            profile.common_2_circuit_total_count,
            profile.common_3_circuit_total_count,
        )
        if any(value is not None for value in explicit_counts):
            return sum(max(0, int(value or 0)) for value in explicit_counts)

        configured_total = int(profile.common_output_circuit_count or 0) + int(profile.split_output_circuit_count or 0)
        return configured_total or 24

    @staticmethod
    def _build_capacitor_bank_circuit_summary(
        telemetry: Optional[CapacitorBankTelemetry],
        profile: Optional[CapacitorBankControlProfile],
    ) -> dict[str, Any]:
        total_count = max(1, CompensationMonitorService._get_configured_capacitor_bank_circuit_total(profile))
        if telemetry is not None and telemetry.running_circuit_count is not None:
            return {
                "running_count": int(telemetry.running_circuit_count),
                "total_count": total_count,
                "has_realtime_state": True,
                "source": "telemetry",
                "state": "live",
            }

        bitmask_values = (
            getattr(telemetry, "circuit_state_phase_a", None),
            getattr(telemetry, "circuit_state_phase_b", None),
            getattr(telemetry, "circuit_state_phase_c", None),
            getattr(telemetry, "circuit_state_common_1", None),
            getattr(telemetry, "circuit_state_common_2", None),
            getattr(telemetry, "circuit_state_common_3", None),
        )
        if any(value is not None for value in bitmask_values):
            running_count = sum(CompensationMonitorService._count_active_bits(value) for value in bitmask_values)
            return {
                "running_count": running_count,
                "total_count": total_count,
                "has_realtime_state": True,
                "source": "telemetry",
                "state": "live",
            }

        profile_running_count = getattr(profile, "running_circuit_count", None)
        if profile_running_count is None and profile is not None:
            profile_running_values = (
                profile.phase_a_circuit_running_count,
                profile.phase_b_circuit_running_count,
                profile.phase_c_circuit_running_count,
                profile.common_group_1_running_count,
                profile.common_group_2_running_count,
                profile.common_group_3_running_count,
            )
            if any(value is not None for value in profile_running_values):
                profile_running_count = sum(max(0, int(value or 0)) for value in profile_running_values)

        if profile_running_count is not None:
            running_count = max(0, min(total_count, int(profile_running_count)))
            return {
                "running_count": running_count,
                "total_count": total_count,
                "has_realtime_state": True,
                "source": "profile",
                "state": "live",
            }

        return {
            "running_count": 0,
            "total_count": total_count,
            "has_realtime_state": False,
            "source": "configured_fallback",
            "state": "mock",
        }

    @staticmethod
    def _build_capacitor_bank_temperature_health(
        telemetry: Optional[CapacitorBankTelemetry],
        profile: Optional[CapacitorBankControlProfile],
        *,
        cabinet_temperature: Optional[float],
    ) -> dict[str, Any]:
        temp_alarm = getattr(telemetry, "temp_alarm", None)
        if temp_alarm is True:
            return CompensationMonitorService._build_metric("温度告警", source="telemetry", state="live")

        threshold = getattr(profile, "temperature_upper_limit", None)
        if cabinet_temperature is None:
            return CompensationMonitorService._build_metric("待判断", source="missing", state="missing")

        if threshold is not None:
            current = float(cabinet_temperature)
            upper_limit = float(threshold)
            warning_margin = max(0.0, float(settings.compensation_temperature_warning_margin_c or 0.0))
            if current >= upper_limit:
                return CompensationMonitorService._build_metric("超过上限", source="profile", state="live")
            if current >= upper_limit - warning_margin:
                return CompensationMonitorService._build_metric("接近上限", source="profile", state="live")
            return CompensationMonitorService._build_metric("正常", source="profile", state="live")

        if temp_alarm is False:
            return CompensationMonitorService._build_metric("正常", source="telemetry", state="live")

        return CompensationMonitorService._build_metric("待判断", source="missing", state="missing")

    @staticmethod
    def _build_capacitor_bank_monitor(
        session: Session,
        device: Device,
        realtime: dict[str, Any],
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
        profile_module_count = int(getattr(profile, "module_count", 0) or 0)
        total_count = profile_module_count if profile_module_count > 0 else None

        capacity_utilization = getattr(telemetry, "capacity_utilization", None)
        capacity_utilization_source = "telemetry"
        capacity_utilization_state = "live"
        if capacity_utilization is None:
            rated_capacity = float(getattr(device, "rated_capacity", 0) or 0)
            reactive_power = realtime.get("reactive_power")
            if rated_capacity > 0 and reactive_power is not None:
                capacity_utilization = round(min(100.0, max(0.0, (abs(float(reactive_power)) / rated_capacity) * 100.0)), 1)
                capacity_utilization_source = "estimated"
                capacity_utilization_state = "mock"
            else:
                capacity_utilization_source = "missing"
                capacity_utilization_state = "missing"

        running_count = None
        circuit_source = "profile" if total_count is not None else "missing"
        circuit_state = "live" if total_count is not None else "missing"
        if capacity_utilization is not None and total_count is not None:
            running_count = max(0, min(total_count, round((float(capacity_utilization) / 100.0) * total_count)))
            circuit_source = capacity_utilization_source
            circuit_state = "live" if capacity_utilization_state == "live" else "mock"

        cabinet_temperature = getattr(telemetry, "cabinet_temp", None)
        cabinet_temperature_source = "telemetry" if cabinet_temperature is not None else "realtime"
        cabinet_temperature_state = "live" if cabinet_temperature is not None else "missing"
        if cabinet_temperature is None:
            cabinet_temperature = realtime.get("temperature")
            if cabinet_temperature is not None:
                cabinet_temperature_state = "live"
            else:
                cabinet_temperature_source = "missing"

        return {
            "subtype": "svg",
            "control_mode": control_mode,
            "circuit_summary": {
                "running_count": running_count,
                "total_count": total_count,
                "has_realtime_state": capacity_utilization is not None and total_count is not None,
                "source": circuit_source,
                "state": circuit_state,
            },
            "profile_status": None,
            "key_metrics": {
                "capacity_utilization": CompensationMonitorService._build_metric(
                    capacity_utilization,
                    source=capacity_utilization_source,
                    state=capacity_utilization_state,
                ),
                "cabinet_temperature": CompensationMonitorService._build_metric(
                    cabinet_temperature,
                    source=cabinet_temperature_source,
                    state=cabinet_temperature_state,
                ),
                "compensation_level": CompensationMonitorService._build_metric(
                    running_count,
                    source=circuit_source,
                    state=circuit_state,
                ),
            },
            "capabilities_summary": SVGService.get_control_capabilities(),
            "status_tags": [],
        }

    @staticmethod
    def build_monitor(
        session: Session,
        device: Device,
        realtime: dict[str, Any],
    ) -> Optional[dict[str, Any]]:
        subtype = resolve_compensation_subtype(
            getattr(device, "device_type", None),
            getattr(device, "device_subtype", None),
        )
        if subtype == "capacitor_bank_controller":
            return CompensationMonitorService._build_capacitor_bank_monitor(session, device, realtime)
        if subtype == "svg":
            return CompensationMonitorService._build_svg_monitor(session, device, realtime)
        return None
