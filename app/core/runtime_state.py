"""
运行时状态与轻量指标。

用于健康检查、生命周期状态暴露和关键链路计数。
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from threading import Lock
from typing import Any, Optional

from app.core.metrics import set_runtime_counter, set_runtime_service_status


class RuntimeState:
    """线程安全的进程内运行时状态存储。"""

    def __init__(self) -> None:
        self._lock = Lock()
        self._state: dict[str, Any] = {
            "services": {
                "database": self._service_payload("unknown"),
                "redis": self._service_payload("unknown"),
                "mqtt": self._service_payload("unknown"),
                "scheduler": self._service_payload("unknown"),
            },
            "counters": {
                "mqtt_messages_total": 0,
                "mqtt_ingestion_success_total": 0,
                "mqtt_ingestion_failure_total": 0,
                "mqtt_duplicates_total": 0,
                "scheduler_job_failures_total": 0,
            },
        }

    @staticmethod
    def _service_payload(status: str, detail: Optional[str] = None) -> dict[str, Any]:
        return {
            "status": status,
            "detail": detail,
            "updated_at": datetime.now().isoformat(),
        }

    def mark_service(self, name: str, status: str, detail: Optional[str] = None) -> None:
        with self._lock:
            self._state["services"][name] = self._service_payload(status, detail)
        set_runtime_service_status(name, status)

    def increment(self, counter_name: str, amount: int = 1) -> None:
        with self._lock:
            counters = self._state["counters"]
            counters[counter_name] = counters.get(counter_name, 0) + amount
            current_value = counters[counter_name]
        set_runtime_counter(counter_name, current_value)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._state)


runtime_state = RuntimeState()
