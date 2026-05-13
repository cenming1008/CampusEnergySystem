"""储能设备监控聚合服务。"""

from __future__ import annotations

from typing import Any, Optional

from sqlmodel import Session, select

from app.models.storage import StorageTelemetry


_RUN_STATE_LABELS: dict[str, str] = {
    "idle": "空闲",
    "charging": "充电中",
    "discharging": "放电中",
    "fault": "故障",
    "standby": "待机",
}


class StorageMonitorService:
    """构建储能设备监控页专属 payload。"""

    @staticmethod
    def _build_metric(value: Any, *, source: str, state: str) -> dict[str, Any]:
        return {"value": value, "source": source, "state": state}

    @staticmethod
    def _telemetry_metric(value: Any) -> dict[str, str]:
        if value is not None:
            return {"source": "telemetry", "state": "live"}
        return {"source": "missing", "state": "missing"}

    @staticmethod
    def _get_latest_telemetry(session: Session, device_id: int) -> Optional[StorageTelemetry]:
        return session.exec(
            select(StorageTelemetry)
            .where(StorageTelemetry.device_id == device_id)
            .order_by(StorageTelemetry.timestamp.desc())
            .limit(1)
        ).first()

    @staticmethod
    def build_storage_monitor(session: Session, device_id: int) -> dict[str, Any]:
        telemetry = StorageMonitorService._get_latest_telemetry(session, device_id)

        soc = getattr(telemetry, "soc", None)
        soh = getattr(telemetry, "soh", None)
        active_power = getattr(telemetry, "active_power", None)
        cell_temp_max = getattr(telemetry, "cell_temp_max", None)
        cell_temp_min = getattr(telemetry, "cell_temp_min", None)
        cell_temp_avg = getattr(telemetry, "cell_temp_avg", None)
        run_state_raw = getattr(telemetry, "run_state", None)
        control_mode = getattr(telemetry, "control_mode", None)
        charge_today = getattr(telemetry, "charge_energy_today", None)
        discharge_today = getattr(telemetry, "discharge_energy_today", None)
        cycle_count = getattr(telemetry, "cycle_count", None)

        run_state_label = _RUN_STATE_LABELS.get(str(run_state_raw or ""), run_state_raw or "未知")

        energy_balance: Optional[float] = None
        if charge_today is not None and discharge_today is not None:
            energy_balance = round(float(charge_today) - float(discharge_today), 2)

        m = StorageMonitorService._build_metric
        tm = StorageMonitorService._telemetry_metric

        return {
            "key_metrics": {
                "soc": m(soc, **tm(soc)),
                "soh": m(soh, **tm(soh)),
                "active_power": m(active_power, **tm(active_power)),
                "cell_temp_max": m(cell_temp_max, **tm(cell_temp_max)),
                "cell_temp_min": m(cell_temp_min, **tm(cell_temp_min)),
                "cell_temp_avg": m(cell_temp_avg, **tm(cell_temp_avg)),
                "run_state": m(
                    run_state_label,
                    source="telemetry" if run_state_raw else "missing",
                    state="live" if run_state_raw else "missing",
                ),
                "control_mode": m(
                    control_mode,
                    source="telemetry" if control_mode else "missing",
                    state="live" if control_mode else "missing",
                ),
                "charge_energy_today": m(charge_today, **tm(charge_today)),
                "discharge_energy_today": m(discharge_today, **tm(discharge_today)),
                "energy_balance_today": m(
                    energy_balance,
                    source="telemetry" if energy_balance is not None else "missing",
                    state="live" if energy_balance is not None else "missing",
                ),
                "cycle_count": m(cycle_count, **tm(cycle_count)),
            },
            "latest_timestamp": getattr(telemetry, "timestamp", None),
            "has_telemetry": telemetry is not None,
        }
