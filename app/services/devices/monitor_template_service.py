"""
设备监控统一模板服务。

该服务只负责把已有设备档案、实时值、专属监控 payload 和接入健康聚合成
前端可统一消费的模板描述，不读取数据库、不改变设备监控主流程。
"""

from __future__ import annotations

from typing import Any, Optional

from app.domain.device_payloads import resolve_compensation_subtype
from app.models.tables import Device
from app.services.devices.monitor_templates import (
    CAPACITOR_BANK_COMMANDS,
    CAPACITOR_BANK_TEMPLATE,
    DRAWABLE_TREND_KEYS,
    GENERIC_TEMPLATE,
    METER_TEMPLATE_REGISTRY,
    MonitorMetricSpec,
    MonitorTemplateSpec,
    STORAGE_STATE_LABELS,
    STORAGE_TEMPLATE,
    SVG_TEMPLATE,
    TEMPLATE_REGISTRY,
)


class MonitorTemplateService:
    """构建设备监控页通用模板描述。"""

    _CAPACITOR_BANK_COMMANDS = CAPACITOR_BANK_COMMANDS
    _DRAWABLE_TREND_KEYS = DRAWABLE_TREND_KEYS
    _GENERIC_TEMPLATE = GENERIC_TEMPLATE
    _CAPACITOR_BANK_TEMPLATE = CAPACITOR_BANK_TEMPLATE
    _SVG_TEMPLATE = SVG_TEMPLATE
    _STORAGE_TEMPLATE = STORAGE_TEMPLATE
    _METER_TEMPLATE_REGISTRY = METER_TEMPLATE_REGISTRY
    _TEMPLATE_REGISTRY = TEMPLATE_REGISTRY
    _STORAGE_STATE_LABELS = STORAGE_STATE_LABELS

    @staticmethod
    def _value_state(value: Any) -> str:
        return "live" if value is not None else "missing"

    @staticmethod
    def _metric(
        *,
        key: str,
        label: str,
        value: Any,
        unit: Optional[str],
        precision: int,
        source: str,
        state: Optional[str] = None,
    ) -> dict[str, Any]:
        return {
            "key": key,
            "label": label,
            "value": value,
            "unit": unit,
            "precision": precision,
            "source": source,
            "state": state or MonitorTemplateService._value_state(value),
        }

    @staticmethod
    def _trend_field(spec: MonitorMetricSpec) -> dict[str, Any]:
        return {
            "key": spec.key,
            "label": spec.label,
            "unit": spec.unit,
            "precision": spec.precision,
        }

    @classmethod
    def _trend_fields(cls, specs: tuple[MonitorMetricSpec, ...]) -> list[dict[str, Any]]:
        return [cls._trend_field(spec) for spec in specs]

    @classmethod
    def get_template_contract_matrix(cls) -> dict[str, dict[str, Any]]:
        """返回模板覆盖矩阵，供契约测试和文档校准使用。"""

        return {
            template_key: {
                "template_key": spec.template_key,
                "category": spec.category,
                "subtype": spec.subtype,
                "display_name": spec.display_name,
                "metric_keys": [item.key for item in spec.metric_specs],
                "trend_keys": [item.key for item in spec.trend_specs],
                "specific_panels": list(spec.specific_panels),
                "supports_remote_control": spec.supports_remote_control,
                "receipt_required": spec.receipt_required,
                "supported_commands": list(spec.supported_commands),
            }
            for template_key, spec in cls._TEMPLATE_REGISTRY.items()
        }

    @staticmethod
    def _is_capacitor_bank(device: Device, compensation_monitor: Optional[dict[str, Any]]) -> bool:
        subtype = resolve_compensation_subtype(
            getattr(device, "device_type", None),
            getattr(device, "device_subtype", None),
        )
        return subtype == "capacitor_bank_controller" or (
            compensation_monitor is not None
            and compensation_monitor.get("subtype") == "capacitor_bank_controller"
        )

    @staticmethod
    def _is_svg(device: Device, compensation_monitor: Optional[dict[str, Any]]) -> bool:
        subtype = resolve_compensation_subtype(
            getattr(device, "device_type", None),
            getattr(device, "device_subtype", None),
        )
        return subtype == "svg" or (
            compensation_monitor is not None
            and compensation_monitor.get("subtype") == "svg"
        )

    @staticmethod
    def _build_capacitor_bank_metric_cards(
        realtime: dict[str, Any],
        compensation_monitor: dict[str, Any],
    ) -> list[dict[str, Any]]:
        cards = [
            MonitorTemplateService._metric(
                key=key,
                label=label,
                value=realtime.get(key),
                unit=unit,
                precision=precision,
                source="realtime",
            )
            for key, label, unit, precision in [
                (item.key, item.label, item.unit, item.precision)
                for item in MonitorTemplateService._CAPACITOR_BANK_TEMPLATE.metric_specs[:4]
            ]
        ]

        circuit_summary = compensation_monitor.get("circuit_summary") or {}
        cards.append(
            MonitorTemplateService._metric(
                key="running_circuit_count",
                label="投入回路",
                value=circuit_summary.get("running_count"),
                unit="路",
                precision=0,
                source=str(circuit_summary.get("source") or "missing"),
                state=str(circuit_summary.get("state") or "missing"),
            )
        )

        capacity_metric = (compensation_monitor.get("key_metrics") or {}).get("capacity_utilization") or {}
        cards.append(
            MonitorTemplateService._metric(
                key="capacity_utilization",
                label="容量利用率",
                value=capacity_metric.get("value"),
                unit="%",
                precision=1,
                source=str(capacity_metric.get("source") or "missing"),
                state=str(capacity_metric.get("state") or "missing"),
            )
        )
        return cards

    @staticmethod
    def _build_generic_metric_cards(realtime: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            MonitorTemplateService._metric(
                key=key,
                label=label,
                value=realtime.get(key),
                unit=unit,
                precision=precision,
                source="realtime" if realtime.get(key) is not None else "missing",
            )
            for key, label, unit, precision in [
                (item.key, item.label, item.unit, item.precision)
                for item in MonitorTemplateService._GENERIC_TEMPLATE.metric_specs
            ]
        ]

    @staticmethod
    def _build_realtime_metric_cards(
        realtime: dict[str, Any],
        specs: tuple[MonitorMetricSpec, ...],
    ) -> list[dict[str, Any]]:
        return [
            MonitorTemplateService._metric(
                key=key,
                label=label,
                value=realtime.get(key),
                unit=unit,
                precision=precision,
                source="realtime" if realtime.get(key) is not None else "missing",
            )
            for key, label, unit, precision in [
                (item.key, item.label, item.unit, item.precision)
                for item in specs
            ]
        ]

    @staticmethod
    def _build_svg_metric_cards(
        realtime: dict[str, Any],
        compensation_monitor: dict[str, Any],
    ) -> list[dict[str, Any]]:
        key_metrics = compensation_monitor.get("key_metrics") or {}
        circuit_summary = compensation_monitor.get("circuit_summary") or {}
        capacity = key_metrics.get("capacity_utilization") or {}
        cabinet_temp = key_metrics.get("cabinet_temperature") or {}

        cards = [
            MonitorTemplateService._metric(
                key="reactive_power",
                label="无功功率",
                value=realtime.get("reactive_power"),
                unit="kvar",
                precision=2,
                source="realtime",
            ),
            MonitorTemplateService._metric(
                key="power_factor",
                label="功率因数",
                value=realtime.get("power_factor"),
                unit=None,
                precision=3,
                source="realtime",
            ),
            MonitorTemplateService._metric(
                key="capacity_utilization",
                label="容量利用率",
                value=capacity.get("value"),
                unit="%",
                precision=1,
                source=str(capacity.get("source") or "missing"),
                state=str(capacity.get("state") or "missing"),
            ),
            MonitorTemplateService._metric(
                key="cabinet_temperature",
                label="柜内温度",
                value=cabinet_temp.get("value"),
                unit="degC",
                precision=1,
                source=str(cabinet_temp.get("source") or "missing"),
                state=str(cabinet_temp.get("state") or "missing"),
            ),
            MonitorTemplateService._metric(
                key="module_count",
                label="模块数",
                value=circuit_summary.get("total_count"),
                unit="个",
                precision=0,
                source=str(circuit_summary.get("source") or "missing"),
                state=str(circuit_summary.get("state") or "missing"),
            ),
        ]
        return cards

    @staticmethod
    def _build_storage_metric_cards(storage_monitor: dict[str, Any]) -> list[dict[str, Any]]:
        key_metrics = storage_monitor.get("key_metrics") or {}

        def metric_value(key: str) -> Any:
            item = key_metrics.get(key) or {}
            value = item.get("value")
            if key == "run_state":
                return MonitorTemplateService._STORAGE_STATE_LABELS.get(str(value or ""), value)
            return value

        def metric_source(key: str) -> str:
            return str((key_metrics.get(key) or {}).get("source") or "missing")

        def metric_state(key: str) -> str:
            return str((key_metrics.get(key) or {}).get("state") or "missing")

        return [
            MonitorTemplateService._metric(
                key=key,
                label=label,
                value=metric_value(key),
                unit=unit,
                precision=precision,
                source=metric_source(key),
                state=metric_state(key),
            )
            for key, label, unit, precision in [
                (item.key, item.label, item.unit, item.precision)
                for item in MonitorTemplateService._STORAGE_TEMPLATE.metric_specs
            ]
        ]

    @staticmethod
    def _build_capacitor_bank_control_summary(compensation_monitor: dict[str, Any]) -> dict[str, Any]:
        capabilities = compensation_monitor.get("capabilities_summary") or {}
        return {
            "supports_remote_control": bool(capabilities.get("supports_remote_control")),
            "receipt_required": True,
            "supported_commands": list(MonitorTemplateService._CAPACITOR_BANK_COMMANDS),
        }

    @staticmethod
    def _build_generic_control_summary() -> dict[str, Any]:
        return {
            "supports_remote_control": False,
            "receipt_required": False,
            "supported_commands": [],
        }

    @staticmethod
    def _build_monitor_template(
        spec: MonitorTemplateSpec,
        *,
        category: Optional[str],
        subtype: Optional[str],
    ) -> dict[str, Any]:
        return {
            "template_key": spec.template_key,
            "category": category or spec.category,
            "subtype": subtype if subtype is not None else spec.subtype,
            "display_name": spec.display_name,
            "specific_panels": list(spec.specific_panels),
        }

    @staticmethod
    def _build_payload(
        spec: MonitorTemplateSpec,
        *,
        category: Optional[str],
        subtype: Optional[str],
        metric_cards: list[dict[str, Any]],
        control_summary: dict[str, Any],
        runtime_status: dict[str, Any],
        ingestion_health: dict[str, Any],
    ) -> dict[str, Any]:
        monitor_template = MonitorTemplateService._build_monitor_template(
            spec,
            category=category,
            subtype=subtype,
        )
        trend_fields = MonitorTemplateService._trend_fields(spec.trend_specs)
        diagnostics_summary = MonitorTemplateService._build_diagnostics_summary(
            runtime_status,
            ingestion_health,
        )
        return {
            "monitor_template": monitor_template,
            "metric_cards": metric_cards,
            "trend_fields": trend_fields,
            "control_summary": control_summary,
            "diagnostics_summary": diagnostics_summary,
            "template_diagnostics": MonitorTemplateService._build_template_diagnostics(
                monitor_template=monitor_template,
                metric_cards=metric_cards,
                trend_fields=trend_fields,
                diagnostics_summary=diagnostics_summary,
            ),
        }

    @staticmethod
    def _build_template_diagnostics(
        *,
        monitor_template: dict[str, Any],
        metric_cards: list[dict[str, Any]],
        trend_fields: list[dict[str, Any]],
        diagnostics_summary: dict[str, Any],
    ) -> dict[str, Any]:
        missing_metric_keys = [
            str(item.get("key"))
            for item in metric_cards
            if item.get("state") == "missing" or item.get("value") is None
        ]
        total_metrics = len(metric_cards)
        missing_metrics = len(missing_metric_keys)
        live_metrics = max(total_metrics - missing_metrics, 0)

        declared_trend_keys = [str(item.get("key")) for item in trend_fields]
        drawable_keys = [
            key
            for key in declared_trend_keys
            if key in MonitorTemplateService._DRAWABLE_TREND_KEYS
        ]
        unsupported_keys = [
            key
            for key in declared_trend_keys
            if key not in MonitorTemplateService._DRAWABLE_TREND_KEYS
        ]

        is_online = diagnostics_summary.get("is_online")
        ingestion_status = diagnostics_summary.get("ingestion_status")
        if is_online is False or ingestion_status == "offline":
            overall_status = "offline"
        elif total_metrics > 0 and live_metrics == 0:
            overall_status = "missing"
        elif missing_metrics > 0 or unsupported_keys:
            overall_status = "partial"
        else:
            overall_status = "passed"

        return {
            "template_key": monitor_template.get("template_key"),
            "display_name": monitor_template.get("display_name"),
            "category": monitor_template.get("category"),
            "subtype": monitor_template.get("subtype"),
            "metric_coverage": {
                "total": total_metrics,
                "live": live_metrics,
                "missing": missing_metrics,
                "missing_keys": missing_metric_keys,
            },
            "trend_coverage": {
                "declared_keys": declared_trend_keys,
                "drawable_keys": drawable_keys,
                "unsupported_keys": unsupported_keys,
            },
            "panel_coverage": {
                "specific_panels": list(monitor_template.get("specific_panels") or []),
            },
            "ingestion_health": diagnostics_summary,
            "overall_status": overall_status,
        }

    @staticmethod
    def _build_diagnostics_summary(
        runtime_status: dict[str, Any],
        ingestion_health: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "ingestion_status": runtime_status.get("ingestion_status") or ingestion_health.get("status"),
            "is_online": bool(runtime_status.get("is_online") or ingestion_health.get("is_online")),
            "last_message_at": runtime_status.get("last_message_at") or ingestion_health.get("last_message_at"),
            "last_success_at": runtime_status.get("last_success_at") or ingestion_health.get("last_success_at"),
        }

    @staticmethod
    def build_overview_template(
        *,
        device: Device,
        realtime: dict[str, Any],
        runtime_status: dict[str, Any],
        ingestion_health: dict[str, Any],
        compensation_monitor: Optional[dict[str, Any]] = None,
        storage_monitor: Optional[dict[str, Any]] = None,
        monitor_plugin: Optional[Any] = None,
        specific_monitor: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """构建追加到 monitor overview 顶层的统一模板 payload。"""

        category = getattr(device, "device_category", None)
        subtype = getattr(device, "device_subtype", None)

        if monitor_plugin is not None:
            spec = monitor_plugin.get_template_spec()
            plugin_key = getattr(monitor_plugin, "plugin_key", spec.template_key)
            template_category = (
                category or getattr(device, "energy_type", None) or getattr(device, "device_type", None)
                if plugin_key == "generic_device"
                else category
            )
            template_subtype = spec.subtype if spec.subtype is not None else subtype
            monitor_payload = specific_monitor or compensation_monitor or storage_monitor
            return MonitorTemplateService._build_payload(
                spec,
                category=template_category,
                subtype=template_subtype,
                metric_cards=monitor_plugin.build_metric_cards(realtime, monitor_payload),
                control_summary=monitor_plugin.get_control_summary(monitor_payload),
                runtime_status=runtime_status,
                ingestion_health=ingestion_health,
            )

        if MonitorTemplateService._is_svg(device, compensation_monitor):
            compensation_payload = compensation_monitor or {}
            spec = MonitorTemplateService._SVG_TEMPLATE
            return MonitorTemplateService._build_payload(
                spec,
                category=category,
                subtype="svg",
                metric_cards=MonitorTemplateService._build_svg_metric_cards(
                    realtime,
                    compensation_payload,
                ),
                control_summary=MonitorTemplateService._build_generic_control_summary(),
                runtime_status=runtime_status,
                ingestion_health=ingestion_health,
            )

        if MonitorTemplateService._is_capacitor_bank(device, compensation_monitor):
            compensation_payload = compensation_monitor or {}
            spec = MonitorTemplateService._CAPACITOR_BANK_TEMPLATE
            return MonitorTemplateService._build_payload(
                spec,
                category=category,
                subtype="capacitor_bank_controller",
                metric_cards=MonitorTemplateService._build_capacitor_bank_metric_cards(
                    realtime,
                    compensation_payload,
                ),
                control_summary=MonitorTemplateService._build_capacitor_bank_control_summary(compensation_payload),
                runtime_status=runtime_status,
                ingestion_health=ingestion_health,
            )

        if category == "storage":
            storage_payload = storage_monitor or {}
            spec = MonitorTemplateService._STORAGE_TEMPLATE
            return MonitorTemplateService._build_payload(
                spec,
                category=category,
                subtype=subtype,
                metric_cards=MonitorTemplateService._build_storage_metric_cards(storage_payload),
                control_summary=MonitorTemplateService._build_generic_control_summary(),
                runtime_status=runtime_status,
                ingestion_health=ingestion_health,
            )

        if category in MonitorTemplateService._METER_TEMPLATE_REGISTRY:
            spec = MonitorTemplateService._METER_TEMPLATE_REGISTRY[category]
            return MonitorTemplateService._build_payload(
                spec,
                category=category,
                subtype=subtype,
                metric_cards=MonitorTemplateService._build_realtime_metric_cards(realtime, spec.metric_specs),
                control_summary=MonitorTemplateService._build_generic_control_summary(),
                runtime_status=runtime_status,
                ingestion_health=ingestion_health,
            )

        return MonitorTemplateService._build_payload(
            MonitorTemplateService._GENERIC_TEMPLATE,
            category=category or getattr(device, "energy_type", None) or getattr(device, "device_type", None),
            subtype=subtype,
            metric_cards=MonitorTemplateService._build_generic_metric_cards(realtime),
            control_summary=MonitorTemplateService._build_generic_control_summary(),
            runtime_status=runtime_status,
            ingestion_health=ingestion_health,
        )


__all__ = ["MonitorMetricSpec", "MonitorTemplateService", "MonitorTemplateSpec"]
