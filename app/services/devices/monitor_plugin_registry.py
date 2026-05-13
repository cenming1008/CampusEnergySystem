"""
设备监控插件注册表。

第一阶段插件是代码内注册：新增设备类型通过新增插件类并加入默认注册表生效，
不支持运行时外部插件或动态路由注册。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Protocol

from sqlmodel import Session

from app.domain.device_payloads import normalize_device_type_alias, resolve_compensation_subtype
from app.models.tables import Device
from app.services.devices.compensation.monitor_service import CompensationMonitorService
from app.services.devices.monitor_template_service import MonitorTemplateService, MonitorTemplateSpec
from app.services.devices.storage.monitor_service import StorageMonitorService


@dataclass(frozen=True)
class DeviceMonitorContext:
    session: Session
    device: Device
    realtime: dict[str, Any]
    runtime_status: dict[str, Any]
    ingestion_health: dict[str, Any]


class DeviceMonitorPlugin(Protocol):
    plugin_key: str

    def match(self, device: Device) -> bool:
        ...

    def build_monitor_payload(
        self,
        context: DeviceMonitorContext,
    ) -> Optional[dict[str, Any]]:
        ...

    def get_template_spec(self) -> MonitorTemplateSpec:
        ...

    def build_metric_cards(
        self,
        realtime: dict[str, Any],
        specific_monitor: Optional[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        ...

    def get_control_summary(self, specific_monitor: Optional[dict[str, Any]]) -> dict[str, Any]:
        ...


class _BaseMonitorPlugin:
    plugin_key = "generic_device"

    def match(self, device: Device) -> bool:
        return False

    def build_monitor_payload(
        self,
        context: DeviceMonitorContext,
    ) -> Optional[dict[str, Any]]:
        return None

    def get_template_spec(self) -> MonitorTemplateSpec:
        return MonitorTemplateService._GENERIC_TEMPLATE

    def build_metric_cards(
        self,
        realtime: dict[str, Any],
        specific_monitor: Optional[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return MonitorTemplateService._build_generic_metric_cards(realtime)

    def get_control_summary(self, specific_monitor: Optional[dict[str, Any]]) -> dict[str, Any]:
        return MonitorTemplateService._build_generic_control_summary()


class _CapacitorBankMonitorPlugin(_BaseMonitorPlugin):
    plugin_key = "capacitor_bank_controller"

    def match(self, device: Device) -> bool:
        return _compensation_subtype(device) == self.plugin_key

    def build_monitor_payload(
        self,
        context: DeviceMonitorContext,
    ) -> Optional[dict[str, Any]]:
        return CompensationMonitorService.build_monitor(context.session, context.device, context.realtime)

    def get_template_spec(self) -> MonitorTemplateSpec:
        return MonitorTemplateService._CAPACITOR_BANK_TEMPLATE

    def build_metric_cards(
        self,
        realtime: dict[str, Any],
        specific_monitor: Optional[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return MonitorTemplateService._build_capacitor_bank_metric_cards(
            realtime,
            specific_monitor or {},
        )

    def get_control_summary(self, specific_monitor: Optional[dict[str, Any]]) -> dict[str, Any]:
        return MonitorTemplateService._build_capacitor_bank_control_summary(specific_monitor or {})


class _SvgMonitorPlugin(_BaseMonitorPlugin):
    plugin_key = "svg"

    def match(self, device: Device) -> bool:
        return _compensation_subtype(device) == self.plugin_key

    def build_monitor_payload(
        self,
        context: DeviceMonitorContext,
    ) -> Optional[dict[str, Any]]:
        return CompensationMonitorService.build_monitor(context.session, context.device, context.realtime)

    def get_template_spec(self) -> MonitorTemplateSpec:
        return MonitorTemplateService._SVG_TEMPLATE

    def build_metric_cards(
        self,
        realtime: dict[str, Any],
        specific_monitor: Optional[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return MonitorTemplateService._build_svg_metric_cards(
            realtime,
            specific_monitor or {},
        )


class _StorageMonitorPlugin(_BaseMonitorPlugin):
    plugin_key = "storage"

    def match(self, device: Device) -> bool:
        return _identity_value(device, "device_category") == self.plugin_key

    def build_monitor_payload(
        self,
        context: DeviceMonitorContext,
    ) -> Optional[dict[str, Any]]:
        return StorageMonitorService.build_storage_monitor(context.session, context.device.id)

    def get_template_spec(self) -> MonitorTemplateSpec:
        return MonitorTemplateService._STORAGE_TEMPLATE

    def build_metric_cards(
        self,
        realtime: dict[str, Any],
        specific_monitor: Optional[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return MonitorTemplateService._build_storage_metric_cards(specific_monitor or {})


class _MeterMonitorPlugin(_BaseMonitorPlugin):
    def __init__(self, template_key: str):
        self.plugin_key = template_key

    def match(self, device: Device) -> bool:
        return (
            _identity_value(device, "device_category") == self.plugin_key
            or _effective_device_type(device) == self.plugin_key
        )

    def get_template_spec(self) -> MonitorTemplateSpec:
        return MonitorTemplateService._METER_TEMPLATE_REGISTRY[self.plugin_key]

    def build_metric_cards(
        self,
        realtime: dict[str, Any],
        specific_monitor: Optional[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return MonitorTemplateService._build_realtime_metric_cards(
            realtime,
            self.get_template_spec().metric_specs,
        )


class _GenericMonitorPlugin(_BaseMonitorPlugin):
    plugin_key = "generic_device"

    def match(self, device: Device) -> bool:
        return True


def _identity_value(device: Device, field_name: str) -> str:
    return str(getattr(device, field_name, "") or "").strip()


def _compensation_subtype(device: Device) -> Optional[str]:
    return resolve_compensation_subtype(
        getattr(device, "device_type", None),
        getattr(device, "device_subtype", None),
    )


def _effective_device_type(device: Device) -> Optional[str]:
    subtype = _compensation_subtype(device)
    if subtype:
        return subtype
    return normalize_device_type_alias(getattr(device, "device_type", None))


class DeviceMonitorPluginRegistry:
    """按设备身份选择监控插件。"""

    _SUBTYPE_PLUGINS: dict[str, DeviceMonitorPlugin] = {
        "capacitor_bank_controller": _CapacitorBankMonitorPlugin(),
        "svg": _SvgMonitorPlugin(),
    }
    _CATEGORY_PLUGINS: dict[str, DeviceMonitorPlugin] = {
        "storage": _StorageMonitorPlugin(),
        **{
            template_key: _MeterMonitorPlugin(template_key)
            for template_key in MonitorTemplateService._METER_TEMPLATE_REGISTRY
        },
    }
    _GENERIC_PLUGIN: DeviceMonitorPlugin = _GenericMonitorPlugin()

    @classmethod
    def resolve(cls, device: Device) -> DeviceMonitorPlugin:
        subtype = _identity_value(device, "device_subtype")
        if subtype in cls._SUBTYPE_PLUGINS:
            return cls._SUBTYPE_PLUGINS[subtype]

        category = _identity_value(device, "device_category")
        if category in cls._CATEGORY_PLUGINS:
            return cls._CATEGORY_PLUGINS[category]

        effective_type = _effective_device_type(device)
        if effective_type in cls._SUBTYPE_PLUGINS:
            return cls._SUBTYPE_PLUGINS[effective_type]
        if effective_type in cls._CATEGORY_PLUGINS:
            return cls._CATEGORY_PLUGINS[effective_type]

        return cls._GENERIC_PLUGIN


__all__ = ["DeviceMonitorContext", "DeviceMonitorPlugin", "DeviceMonitorPluginRegistry"]
