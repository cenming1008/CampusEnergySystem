#!/usr/bin/env python3
"""
批量重试 MQTT 失败/死信记录。
"""

from __future__ import annotations

import argparse
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="批量重试 MQTT 失败/死信记录")
    parser.add_argument("--limit", type=int, default=20, help="最多处理多少条记录")
    parser.add_argument("--device-id", type=int, default=None, help="仅处理指定设备")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    processed = 0

    with Session(engine) as session:
        records = MqttReliabilityService.list_retry_ready_records(
            session,
            limit=max(1, args.limit),
            device_id=args.device_id,
        )

        for record in records:
            if not record.raw_payload:
                continue
            payload = parse_payload(record.raw_payload)
            if payload is None:
                continue
            process_payload_dict(payload, topic=record.topic, raw_payload=record.raw_payload)
            refreshed = MqttReliabilityService.get_record_by_id(session, record.id)
            if refreshed is not None:
                MqttReliabilityService.mark_replayed(session, refreshed)
                session.commit()
            processed += 1

    print(f"replayed_records={processed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
