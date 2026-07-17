"""Exact-device removal of allowlisted storage simulation business rows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import delete
from sqlmodel import Session, select

from app.models.storage import StorageAssetProfile, StorageDispatchPlan, StorageTelemetry
from app.models.tables import AuditEvent, Device, DeviceControlLog


@dataclass(frozen=True)
class CutoverCounts:
    telemetry_count: int = 0
    plan_count: int = 0
    control_log_count: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "telemetry": self.telemetry_count,
            "plans": self.plan_count,
            "control_logs": self.control_log_count,
        }


@dataclass(frozen=True)
class CutoverResult:
    deleted: CutoverCounts
    device_id: int
    operator: str
    executed_at: datetime


class StorageSimulationCutoverService:
    """Preview first and delete only explicitly allowlisted simulated records."""

    SIMULATOR_ACTIVE_WINDOW = timedelta(minutes=5)

    @staticmethod
    def _structured_simulated_log(log: DeviceControlLog) -> bool:
        try:
            reason: Any = json.loads(log.reason or "")
        except (TypeError, json.JSONDecodeError):
            return False
        return isinstance(reason, dict) and reason.get("data_source") == "simulated"

    @staticmethod
    def _control_logs(session: Session, device_id: int, *, lock: bool = False) -> list[DeviceControlLog]:
        statement = (
            select(DeviceControlLog)
            .where(DeviceControlLog.device_id == device_id)
            .where(DeviceControlLog.command_source == "storage-control-api")
        )
        if lock:
            statement = statement.with_for_update()
        return [
            log
            for log in session.exec(statement).all()
            if StorageSimulationCutoverService._structured_simulated_log(log)
        ]

    @staticmethod
    def _counts(session: Session, device_id: int, *, lock: bool = False) -> CutoverCounts:
        telemetry_statement = (
            select(StorageTelemetry)
            .where(StorageTelemetry.device_id == device_id)
            .where(StorageTelemetry.data_source == "simulated")
        )
        plan_statement = (
            select(StorageDispatchPlan)
            .where(StorageDispatchPlan.device_id == device_id)
            .where(StorageDispatchPlan.data_source == "simulated")
        )
        if lock:
            telemetry_statement = telemetry_statement.with_for_update()
            plan_statement = plan_statement.with_for_update()
        telemetry = session.exec(telemetry_statement).all()
        plans = session.exec(plan_statement).all()
        logs = StorageSimulationCutoverService._control_logs(session, device_id, lock=lock)
        return CutoverCounts(len(telemetry), len(plans), len(logs))

    @staticmethod
    def _require_storage_device(session: Session, device_id: int, *, lock: bool = False) -> Device:
        statement = select(Device).where(Device.id == device_id)
        if lock:
            statement = statement.with_for_update()
        device = session.exec(statement).one_or_none()
        if device is None:
            raise ValueError("设备不存在。")
        if device.device_category != "storage":
            raise ValueError("仅 device_category=storage 的设备允许执行切换。")
        return device

    @staticmethod
    def preview(session: Session, device_id: int) -> CutoverCounts:
        StorageSimulationCutoverService._require_storage_device(session, device_id)
        return StorageSimulationCutoverService._counts(session, device_id)

    @staticmethod
    def _check_blockers(session: Session, device_id: int, now: datetime) -> None:
        profile = session.exec(
            select(StorageAssetProfile)
            .where(StorageAssetProfile.device_id == device_id)
            .with_for_update()
        ).one_or_none()
        if profile is not None and profile.ems_auto_enabled:
            raise ValueError("设备级 EMS 自动控制仍开启，拒绝切换。")
        recent = session.exec(
            select(StorageTelemetry)
            .where(StorageTelemetry.device_id == device_id)
            .where(StorageTelemetry.data_source == "simulated")
            .where(StorageTelemetry.timestamp >= now - StorageSimulationCutoverService.SIMULATOR_ACTIVE_WINDOW)
            .limit(1)
            .with_for_update()
        ).first()
        if recent is not None:
            raise ValueError("近期 simulated 遥测表明模拟器仍活跃，拒绝切换。")

    @staticmethod
    def execute(
        session: Session,
        device_id: int,
        expected: CutoverCounts,
        operator: str,
    ) -> CutoverResult:
        normalized_operator = (operator or "").strip()
        if not normalized_operator:
            raise ValueError("operator 必须显式提供。")
        if not isinstance(expected, CutoverCounts):
            raise ValueError("expected 必须来自显式预览计数。")

        executed_at = datetime.now()
        try:
            StorageSimulationCutoverService._require_storage_device(session, device_id, lock=True)
            StorageSimulationCutoverService._check_blockers(session, device_id, executed_at)
            actual = StorageSimulationCutoverService._counts(session, device_id, lock=True)
            if actual != expected:
                raise ValueError(
                    f"预览计数发生漂移：expected={expected.as_dict()} actual={actual.as_dict()}。"
                )

            log_ids = [
                log.id
                for log in StorageSimulationCutoverService._control_logs(session, device_id, lock=True)
                if log.id is not None
            ]
            session.exec(
                delete(StorageTelemetry)
                .where(StorageTelemetry.device_id == device_id)
                .where(StorageTelemetry.data_source == "simulated")
            )
            session.exec(
                delete(StorageDispatchPlan)
                .where(StorageDispatchPlan.device_id == device_id)
                .where(StorageDispatchPlan.data_source == "simulated")
            )
            if log_ids:
                session.exec(delete(DeviceControlLog).where(DeviceControlLog.id.in_(log_ids)))
            session.add(
                AuditEvent(
                    action="storage.simulation_cutover",
                    actor=normalized_operator,
                    target=f"device:{device_id}",
                    outcome="success",
                    details=json.dumps(
                        {
                            "device_id": device_id,
                            "operator": normalized_operator,
                            "counts": actual.as_dict(),
                            "timestamp": executed_at.isoformat(),
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                )
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        return CutoverResult(
            deleted=actual,
            device_id=device_id,
            operator=normalized_operator,
            executed_at=executed_at,
        )


__all__ = ["CutoverCounts", "CutoverResult", "StorageSimulationCutoverService"]
