#!/usr/bin/env python3
"""Run a deterministic local storage day and write auditable demo artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlmodel import Session, SQLModel, create_engine  # noqa: E402

from app.domain.storage_simulation import StorageState  # noqa: E402
from app.models.storage import StorageAssetProfile  # noqa: E402
from app.models.tables import Device  # noqa: E402
from scripts.python.storage_simulator import (  # noqa: E402
    SCENARIO_NAMES,
    SimulatorConfig,
    StorageSimulator,
)


class _CaptureClient:
    def __init__(self) -> None:
        self.payloads: list[dict[str, Any]] = []

    def publish(self, _topic: str, payload: str, qos: int = 1) -> None:
        del qos
        self.payloads.append(json.loads(payload))


def _comparison(scenario: str, seed: int) -> dict[str, Any]:
    # The demo uses only its in-memory engine, but the legacy app.services package
    # initializes the application engine while importing the shared comparison service.
    os.environ.setdefault(
        "DATABASE_URL", "postgresql://storage_demo:storage_demo@localhost/storage_demo"
    )
    from app.services.storage_energy_service import StorageEnergyService

    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        device = Device(
            name="储能演示设备",
            sn="STO-DEMO-001",
            device_type="storage",
            device_subtype="battery_energy_storage_system",
            device_category="storage",
            energy_type="electricity",
        )
        session.add(device)
        session.commit()
        session.refresh(device)
        session.add(
            StorageAssetProfile(
                device_id=device.id,
                rated_energy_kwh=500,
                rated_power_kw=250,
                max_charge_power_kw=250,
                max_discharge_power_kw=250,
            )
        )
        session.commit()
        return StorageEnergyService.compare_strategies(
            session,
            scenario_key=scenario,
            seed=seed,
            initial_soc=50.0,
            allowed_device_ids={device.id},
            device_id=device.id,
        )


def _receipt_invariants(config: SimulatorConfig) -> tuple[bool, bool]:
    simulator = StorageSimulator(config)
    capture = _CaptureClient()
    simulator.client = capture
    simulator._handle_real_control(
        {"command_id": "demo-terminal", "command": "set_active_power", "target_active_power": 0}
    )
    for _ in range(3):
        simulator.advance_one_step()
    terminal = any(
        payload.get("command_id") == "demo-terminal" and payload.get("status") == "success"
        for payload in capture.payloads
    )

    simulator.state = replace(StorageState(soc=simulator.asset.soc_min), actual_power_kw=0.0)
    simulator._handle_real_control(
        {"command_id": "demo-safety", "command": "set_active_power", "target_active_power": -10}
    )
    rejected = any(
        payload.get("command_id") == "demo-safety" and payload.get("status") == "rejected"
        for payload in capture.payloads
    )
    return terminal, rejected


def run_demo(*, scenario: str, speed: float, seed: int, output_dir: Path | str) -> dict[str, Any]:
    config = SimulatorConfig(
        scenario=scenario,
        speed=speed,
        seed=seed,
        telemetry_interval_seconds=900.0,
    )
    simulator = StorageSimulator(config)
    simulator.simulation_run_id = f"demo-{scenario}-{seed}"
    base_timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(
        days=seed % 3650
    )
    payloads = []
    for slot_index in range(96):
        payload = simulator.advance_one_step()
        payload["timestamp"] = (base_timestamp + timedelta(minutes=15 * slot_index)).isoformat()
        payloads.append(payload)
    comparison = _comparison(scenario, seed)
    terminal_receipt, safety_rejection = _receipt_invariants(config)
    powers = [float(payload["active_power"]) for payload in payloads]
    soc_values = [float(payload["soc"]) for payload in payloads]
    midday = powers[40:60]
    evening = powers[72:84]
    invariants = {
        "midday_charge": any(power > 0 for power in midday),
        "evening_discharge": any(power < 0 for power in evening),
        "soc_hard_bounds": min(soc_values) >= 10.0 and max(soc_values) <= 90.0,
        "safety_rejection": safety_rejection,
        "terminal_receipt": terminal_receipt,
        "calculated_comparison": comparison.get("data_source") == "calculated",
        "persistent_simulated_label": all(
            payload.get("data_source") == "simulated" and payload.get("simulation_run_id")
            for payload in payloads
        ),
    }
    summary = {
        "scenario": scenario,
        "speed": speed,
        "seed": seed,
        "slots": len(payloads),
        "min_soc": min(soc_values),
        "max_soc": max(soc_values),
        "invariants": invariants,
        "comparison": comparison,
        "last_payload": payloads[-1],
    }
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "storage-demo-raw.json").write_text(
        json.dumps(payloads, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    with (destination / "storage-demo-raw.csv").open("w", encoding="utf-8", newline="") as handle:
        fieldnames = sorted({key for payload in payloads for key in payload})
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(payloads)
    (destination / "storage-demo-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    return summary


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic campus storage demo")
    parser.add_argument("--scenario", choices=SCENARIO_NAMES, default="sunny_workday")
    parser.add_argument("--speed", type=float, default=5760.0)
    parser.add_argument("--seed", type=int, default=20260716)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    summary = run_demo(
        scenario=args.scenario,
        speed=args.speed,
        seed=args.seed,
        output_dir=args.output_dir,
    )
    print(json.dumps(summary, ensure_ascii=False, default=str, sort_keys=True))
    return 0 if all(summary["invariants"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
