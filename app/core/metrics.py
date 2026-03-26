"""
Prometheus 指标注册与采集。
"""

from __future__ import annotations

from collections import defaultdict
from threading import Lock

try:
    from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, generate_latest
    _PROMETHEUS_AVAILABLE = True
except Exception:
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
    _PROMETHEUS_AVAILABLE = False

    class _MetricHandle:
        def __init__(self, metric: "_FallbackMetric", label_values: tuple[str, ...]) -> None:
            self.metric = metric
            self.label_values = label_values

        def inc(self, amount: float = 1.0) -> None:
            self.metric.inc(self.label_values, amount)

        def observe(self, value: float) -> None:
            self.metric.observe(self.label_values, value)

        def set(self, value: float) -> None:
            self.metric.set(self.label_values, value)


    class _FallbackMetric:
        def __init__(self, name: str, documentation: str, labelnames: tuple[str, ...] = ()) -> None:
            self.name = name
            self.documentation = documentation
            self.labelnames = labelnames
            self._values: dict[tuple[str, ...], float] = defaultdict(float)
            self._lock = Lock()

        def labels(self, **kwargs: str) -> _MetricHandle:
            label_values = tuple(str(kwargs[label]) for label in self.labelnames)
            return _MetricHandle(self, label_values)

        def inc(self, label_values: tuple[str, ...], amount: float = 1.0) -> None:
            with self._lock:
                self._values[label_values] += amount

        def observe(self, label_values: tuple[str, ...], value: float) -> None:
            with self._lock:
                self._values[label_values] += value

        def set(self, label_values: tuple[str, ...], value: float) -> None:
            with self._lock:
                self._values[label_values] = value

        def render(self) -> list[str]:
            lines = [
                f"# HELP {self.name} {self.documentation}",
                f"# TYPE {self.name} gauge",
            ]
            with self._lock:
                items = list(self._values.items())
            if not items:
                lines.append(f"{self.name} 0.0")
                return lines
            for label_values, value in items:
                if self.labelnames:
                    pairs = ",".join(
                        f'{key}="{val}"' for key, val in zip(self.labelnames, label_values)
                    )
                    lines.append(f"{self.name}{{{pairs}}} {value}")
                else:
                    lines.append(f"{self.name} {value}")
            return lines


    class CollectorRegistry:
        def __init__(self) -> None:
            self.metrics: list[_FallbackMetric] = []

        def register(self, metric: _FallbackMetric) -> None:
            self.metrics.append(metric)


    class Counter(_FallbackMetric):
        def __init__(self, name: str, documentation: str, labelnames: tuple[str, ...] = (), registry: CollectorRegistry | None = None) -> None:
            super().__init__(name, documentation, labelnames)
            if registry is not None:
                registry.register(self)


    class Gauge(_FallbackMetric):
        def __init__(self, name: str, documentation: str, labelnames: tuple[str, ...] = (), registry: CollectorRegistry | None = None) -> None:
            super().__init__(name, documentation, labelnames)
            if registry is not None:
                registry.register(self)


    class Histogram(_FallbackMetric):
        def __init__(
            self,
            name: str,
            documentation: str,
            labelnames: tuple[str, ...] = (),
            buckets: tuple[float, ...] | None = None,
            registry: CollectorRegistry | None = None,
        ) -> None:
            super().__init__(name, documentation, labelnames)
            self.buckets = buckets or ()
            if registry is not None:
                registry.register(self)


    def generate_latest(registry: CollectorRegistry) -> bytes:
        lines: list[str] = []
        for metric in registry.metrics:
            lines.extend(metric.render())
        return ("\n".join(lines) + "\n").encode("utf-8")


registry = CollectorRegistry()

http_requests_total = Counter(
    "mine_http_requests_total",
    "Total HTTP requests handled by the API.",
    labelnames=("method", "path", "status"),
    registry=registry,
)

http_request_duration_seconds = Histogram(
    "mine_http_request_duration_seconds",
    "HTTP request latency in seconds.",
    labelnames=("method", "path"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=registry,
)

mqtt_messages_total = Counter(
    "mine_mqtt_messages_total",
    "MQTT messages processed by status.",
    labelnames=("status",),
    registry=registry,
)

mqtt_processing_duration_seconds = Histogram(
    "mine_mqtt_processing_duration_seconds",
    "MQTT message processing latency in seconds.",
    labelnames=("status",),
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
    registry=registry,
)

scheduler_job_runs_total = Counter(
    "mine_scheduler_job_runs_total",
    "Scheduler job executions by outcome.",
    labelnames=("job_id", "outcome"),
    registry=registry,
)

runtime_service_status = Gauge(
    "mine_runtime_service_status",
    "Runtime service status as a numeric gauge (healthy=1, degraded=0.5, stopped/unknown=0, unhealthy=-1).",
    labelnames=("service",),
    registry=registry,
)

runtime_counter_gauge = Gauge(
    "mine_runtime_counter_value",
    "Runtime counters mirrored as gauges for Prometheus scraping.",
    labelnames=("counter_name",),
    registry=registry,
)

frontend_errors_total = Counter(
    "mine_frontend_errors_total",
    "Frontend errors reported by category.",
    labelnames=("category",),
    registry=registry,
)

_STATUS_VALUE_MAP = {
    "healthy": 1.0,
    "degraded": 0.5,
    "stopped": 0.0,
    "unknown": 0.0,
    "unhealthy": -1.0,
}


def observe_http_request(method: str, path: str, status_code: int, duration_seconds: float) -> None:
    path_label = path or "/"
    http_requests_total.labels(method=method, path=path_label, status=str(status_code)).inc()
    http_request_duration_seconds.labels(method=method, path=path_label).observe(duration_seconds)


def observe_mqtt_message(status: str, duration_seconds: float) -> None:
    mqtt_messages_total.labels(status=status).inc()
    mqtt_processing_duration_seconds.labels(status=status).observe(duration_seconds)


def observe_scheduler_job(job_id: str, outcome: str) -> None:
    scheduler_job_runs_total.labels(job_id=job_id or "unknown", outcome=outcome).inc()


def set_runtime_service_status(service: str, status: str) -> None:
    runtime_service_status.labels(service=service).set(_STATUS_VALUE_MAP.get(status, 0.0))


def set_runtime_counter(counter_name: str, value: int | float) -> None:
    runtime_counter_gauge.labels(counter_name=counter_name).set(value)


def observe_frontend_error(category: str) -> None:
    frontend_errors_total.labels(category=category or "unknown").inc()


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(registry), CONTENT_TYPE_LATEST
