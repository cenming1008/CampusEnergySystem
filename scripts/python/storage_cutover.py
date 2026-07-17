#!/usr/bin/env python3
"""Preview or explicitly execute exact-device storage simulation cutover."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlmodel import Session, select  # noqa: E402


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview or execute exact-device simulated storage data cutover"
    )
    parser.add_argument("--device-code", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preview", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--operator")
    parser.add_argument("--expected-telemetry", type=int)
    parser.add_argument("--expected-plans", type=int)
    parser.add_argument("--expected-control-logs", type=int)
    args = parser.parse_args(argv)
    if args.execute:
        required = {
            "--operator": args.operator,
            "--expected-telemetry": args.expected_telemetry,
            "--expected-plans": args.expected_plans,
            "--expected-control-logs": args.expected_control_logs,
        }
        missing = [name for name, value in required.items() if value is None or value == ""]
        if missing:
            parser.error(f"--execute requires {', '.join(missing)}")
        if any(value < 0 for value in (
            args.expected_telemetry,
            args.expected_plans,
            args.expected_control_logs,
        )):
            parser.error("expected counts must be non-negative")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    from app.core.database import engine
    from app.models.tables import Device
    from app.services.devices.storage.simulation_cutover_service import (
        CutoverCounts,
        StorageSimulationCutoverService,
    )

    with Session(engine) as session:
        device = session.exec(select(Device).where(Device.sn == args.device_code)).one_or_none()
        if device is None:
            raise SystemExit(f"device not found: {args.device_code}")
        if args.preview:
            counts = StorageSimulationCutoverService.preview(session, device.id)
            print(json.dumps({"device_code": args.device_code, **counts.as_dict()}, sort_keys=True))
            return 0
        expected = CutoverCounts(
            telemetry_count=args.expected_telemetry,
            plan_count=args.expected_plans,
            control_log_count=args.expected_control_logs,
        )
        result = StorageSimulationCutoverService.execute(
            session,
            device_id=device.id,
            expected=expected,
            operator=args.operator,
        )
        print(
            json.dumps(
                {
                    "device_code": args.device_code,
                    "deleted": result.deleted.as_dict(),
                    "operator": result.operator,
                    "timestamp": result.executed_at.isoformat(),
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
