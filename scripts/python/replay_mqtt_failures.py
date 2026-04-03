#!/usr/bin/env python3
"""
批量重试 MQTT 失败/死信记录。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlmodel import Session

from app.core.database import engine
from app.integrations.mqtt.processor import parse_payload, process_payload_dict
from app.services.mqtt_reliability_service import MqttReliabilityService
from app.core.runtime_state import runtime_state


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="批量重试 MQTT 失败/死信记录")
    parser.add_argument("--limit", type=int, default=20, help="最多处理多少条记录")
    parser.add_argument("--device-id", type=int, default=None, help="仅处理指定设备")
    return parser.parse_args()


def replay_record(session: Session, record) -> str:
    if not record.raw_payload:
        return "skipped_missing_payload"

    payload = parse_payload(record.raw_payload)
    refreshed = MqttReliabilityService.get_record_by_id(session, record.id)
    if refreshed is None:
        return "failed_missing_record"

    if payload is None:
        MqttReliabilityService.mark_failure(session, refreshed, "replay payload invalid json")
        session.commit()
        return "failed_invalid_payload"

    message = process_payload_dict(payload, topic=record.topic, raw_payload=record.raw_payload)
    refreshed = MqttReliabilityService.get_record_by_id(session, record.id)
    if refreshed is None:
        return "failed_missing_record"
    if message is None:
        MqttReliabilityService.mark_failure(session, refreshed, "replay produced no telemetry event")
        session.commit()
        return "failed_no_event"

    MqttReliabilityService.mark_replayed(session, refreshed)
    session.commit()
    return "replayed"


def main() -> int:
    args = parse_args()
    summary = {
        "requested_records": 0,
        "replayed_records": 0,
        "failed_records": 0,
        "skipped_records": 0,
        "outcomes": {},
    }

    with Session(engine) as session:
        records = MqttReliabilityService.list_retry_ready_records(
            session,
            limit=max(1, args.limit),
            device_id=args.device_id,
        )
        summary["requested_records"] = len(records)

        for record in records:
            outcome = replay_record(session, record)
            summary["outcomes"][outcome] = summary["outcomes"].get(outcome, 0) + 1
            if outcome == "replayed":
                summary["replayed_records"] += 1
                runtime_state.increment("mqtt_replay_success_total")
            elif outcome.startswith("skipped_"):
                summary["skipped_records"] += 1
                runtime_state.increment("mqtt_replay_skipped_total")
            else:
                summary["failed_records"] += 1
                runtime_state.increment("mqtt_replay_failure_total")

    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
