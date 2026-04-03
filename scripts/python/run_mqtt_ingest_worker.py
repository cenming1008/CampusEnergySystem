#!/usr/bin/env python3
"""
独立 MQTT ingest worker 启动入口。
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import init_db
from app.core.logger import logger
from app.core.settings import settings
from app.core.startup_checks import validate_runtime_configuration
from app.services.mqtt_realtime_bridge import WorkerHealthReporter, publish_realtime_event
from app.services.mqtt_worker import start_mqtt_background, stop_mqtt


def main() -> int:
    reporter = WorkerHealthReporter()
    reporter.set_status("starting", "worker booting")
    reporter.start()

    def handle_worker_event(event_name: str, payload: dict[str, object]) -> None:
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        topic = payload.get("topic")
        if event_name == "connected":
            reporter.set_status("healthy", "mqtt worker connected", meta={"last_connected_at": now})
            return
        if event_name in {"connect_retrying", "disconnected", "connect_failed"}:
            reporter.set_status(
                "degraded" if event_name == "connect_retrying" else "unhealthy",
                str(payload.get("error") or payload.get("rc") or event_name),
                meta={"last_error_at": now},
            )
            return
        if event_name == "message_received":
            meta = dict(getattr(reporter, "_meta", {}))
            reporter.record_event(
                consumed_messages_total=int(meta.get("consumed_messages_total", 0)) + 1,
                last_message_at=now,
                last_topic=topic,
            )
            return
        if event_name == "message_processed":
            meta = dict(getattr(reporter, "_meta", {}))
            reporter.record_event(
                processed_messages_total=int(meta.get("processed_messages_total", 0)) + 1,
                last_processed_at=now,
                last_topic=topic,
                last_event_type=payload.get("event_type"),
            )
            return
        if event_name == "message_skipped":
            meta = dict(getattr(reporter, "_meta", {}))
            reporter.record_event(
                skipped_messages_total=int(meta.get("skipped_messages_total", 0)) + 1,
                last_skipped_at=now,
                last_topic=topic,
            )

    def bridge_publish_callback(message: dict[str, object]) -> None:
        try:
            publish_realtime_event(message)
            meta = dict(getattr(reporter, "_meta", {}))
            reporter.record_event(
                published_events_total=int(meta.get("published_events_total", 0)) + 1,
                last_publish_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
                last_event_type=message.get("type"),
            )
        except Exception as exc:
            meta = dict(getattr(reporter, "_meta", {}))
            reporter.record_event(
                publish_failures_total=int(meta.get("publish_failures_total", 0)) + 1,
                last_publish_error_at=time.strftime("%Y-%m-%dT%H:%M:%S"),
                last_error=str(exc),
            )
            raise

    try:
        validate_runtime_configuration(settings)
        init_db()
        reporter.set_status("healthy", "database initialized")

        started = start_mqtt_background(
            on_message_callback=bridge_publish_callback,
            event_callback=handle_worker_event,
        )
        if started:
            reporter.set_status("healthy", "mqtt worker consuming")
        else:
            reporter.set_status("degraded", "mqtt initial connect retrying")

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 收到退出信号，准备停止 MQTT ingest worker")
        return 0
    except Exception as exc:
        reporter.set_status("unhealthy", str(exc))
        logger.exception("❌ MQTT ingest worker 启动失败")
        return 1
    finally:
        try:
            stop_mqtt()
        except Exception as exc:
            logger.warning(f"⚠️ 停止 MQTT worker 失败: {exc}")
        reporter.stop()


if __name__ == "__main__":
    raise SystemExit(main())
