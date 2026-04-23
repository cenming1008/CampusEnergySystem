"""
电容补偿控制器参数快照服务。

负责设备回读参数的快照读写、新鲜度判断与容量阶梯展开，不处理控制命令下发。
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from sqlmodel import Session, select

from app.integrations.jkwf_lcd.capacity import build_capacity_expansion
from app.models.tables import CapacitorBankControlProfile
from app.services.devices.compensation.capacitor_bank.specs import CONTROL_PROFILE_STALE_AFTER


class CapacitorBankControlProfileService:
    """电容补偿控制器参数快照层。"""

    @staticmethod
    def get_control_profile(session: Session, device_id: int) -> Optional[CapacitorBankControlProfile]:
        return session.exec(
            select(CapacitorBankControlProfile).where(CapacitorBankControlProfile.device_id == device_id)
        ).first()

    @staticmethod
    def upsert_control_profile(
        session: Session,
        device_id: int,
        payload: dict[str, Any],
        *,
        snapshot_timestamp: Optional[datetime] = None,
        source: str = "telemetry",
    ) -> CapacitorBankControlProfile:
        profile = CapacitorBankControlProfileService.get_control_profile(session, device_id)
        if profile is None:
            profile = CapacitorBankControlProfile(device_id=device_id)

        for field, value in payload.items():
            if value is None or not hasattr(profile, field):
                continue
            if field.endswith("_capacity_steps_kvar_json"):
                serialized_steps = CapacitorBankControlProfileService._serialize_capacity_steps(value)
                if serialized_steps is None:
                    continue
                setattr(profile, field, serialized_steps)
                continue
            setattr(profile, field, value)

        profile.source = source
        profile.snapshot_timestamp = snapshot_timestamp or datetime.now()
        profile.updated_at = datetime.now()
        session.add(profile)
        return profile

    @staticmethod
    def get_profile_source_status(profile: Optional[CapacitorBankControlProfile]) -> str:
        if profile is None:
            return "empty"
        snapshot = profile.snapshot_timestamp or profile.updated_at
        if snapshot is None:
            return "unknown"
        if datetime.now() - snapshot > CONTROL_PROFILE_STALE_AFTER:
            return "stale"
        return "fresh"

    @staticmethod
    def _serialize_capacity_steps(value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, (list, tuple)):
            normalized = [float(item) for item in value]
            return json.dumps(normalized, ensure_ascii=False)
        return None

    @staticmethod
    def _parse_capacity_steps(value: Any) -> list[float]:
        if value is None:
            return []
        parsed = value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return []
        if not isinstance(parsed, list):
            return []
        result: list[float] = []
        for item in parsed:
            try:
                result.append(float(item))
            except (TypeError, ValueError):
                continue
        return result

    @staticmethod
    def build_direct_capacity_steps_payload(profile: Optional[CapacitorBankControlProfile]) -> dict[str, list[float]]:
        if profile is None:
            return {
                "phase_a_capacity_steps_kvar": [],
                "phase_b_capacity_steps_kvar": [],
                "phase_c_capacity_steps_kvar": [],
                "common_1_capacity_steps_kvar": [],
                "common_2_capacity_steps_kvar": [],
                "common_3_capacity_steps_kvar": [],
            }
        return {
            "phase_a_capacity_steps_kvar": CapacitorBankControlProfileService._parse_capacity_steps(profile.phase_a_capacity_steps_kvar_json),
            "phase_b_capacity_steps_kvar": CapacitorBankControlProfileService._parse_capacity_steps(profile.phase_b_capacity_steps_kvar_json),
            "phase_c_capacity_steps_kvar": CapacitorBankControlProfileService._parse_capacity_steps(profile.phase_c_capacity_steps_kvar_json),
            "common_1_capacity_steps_kvar": CapacitorBankControlProfileService._parse_capacity_steps(profile.common_1_capacity_steps_kvar_json),
            "common_2_capacity_steps_kvar": CapacitorBankControlProfileService._parse_capacity_steps(profile.common_2_capacity_steps_kvar_json),
            "common_3_capacity_steps_kvar": CapacitorBankControlProfileService._parse_capacity_steps(profile.common_3_capacity_steps_kvar_json),
        }

    @staticmethod
    def build_capacity_expansion_payload(profile: Optional[CapacitorBankControlProfile]) -> dict[str, Any]:
        direct_steps = CapacitorBankControlProfileService.build_direct_capacity_steps_payload(profile)
        has_direct_steps = any(direct_steps.values())
        if profile is None:
            return {
                **direct_steps,
                "split_capacity_expansion": {
                    "phase_a_groups": [],
                    "phase_b_groups": [],
                    "phase_c_groups": [],
                },
                "common_capacity_expansion": {
                    "common_1_groups": [],
                    "common_2_groups": [],
                    "common_3_groups": [],
                },
            }
        if has_direct_steps:
            return {
                **direct_steps,
                "split_capacity_expansion": {
                    "phase_a_groups": direct_steps["phase_a_capacity_steps_kvar"],
                    "phase_b_groups": direct_steps["phase_b_capacity_steps_kvar"],
                    "phase_c_groups": direct_steps["phase_c_capacity_steps_kvar"],
                },
                "common_capacity_expansion": {
                    "common_1_groups": direct_steps["common_1_capacity_steps_kvar"],
                    "common_2_groups": direct_steps["common_2_capacity_steps_kvar"],
                    "common_3_groups": direct_steps["common_3_capacity_steps_kvar"],
                },
            }
        return build_capacity_expansion(
            common_capacity_code=profile.common_capacity_code,
            split_capacity_code=profile.split_capacity_code,
            common_step_capacity_kvar=profile.common_step_capacity_kvar,
            split_step_capacity_kvar=profile.split_step_capacity_kvar,
            common_output_circuit_count=profile.common_output_circuit_count,
            split_output_circuit_count=profile.split_output_circuit_count,
            phase_a_circuit_total_count=profile.phase_a_circuit_total_count,
            phase_b_circuit_total_count=profile.phase_b_circuit_total_count,
            phase_c_circuit_total_count=profile.phase_c_circuit_total_count,
            common_1_circuit_total_count=profile.common_1_circuit_total_count,
            common_2_circuit_total_count=profile.common_2_circuit_total_count,
            common_3_circuit_total_count=profile.common_3_circuit_total_count,
        ) | direct_steps
