from types import SimpleNamespace

from app.services.devices.monitor_plugin_registry import DeviceMonitorContext, DeviceMonitorPluginRegistry


def _device(**overrides):
    payload = {
        "device_category": None,
        "device_subtype": None,
        "device_type": None,
        "energy_type": "electricity",
    }
    payload.update(overrides)
    return SimpleNamespace(**payload)


def test_registry_matches_capacitor_bank_by_subtype():
    plugin = DeviceMonitorPluginRegistry.resolve(
        _device(
            device_category="compensation",
            device_subtype="capacitor_bank_controller",
            device_type="compensation",
        )
    )

    assert plugin.plugin_key == "capacitor_bank_controller"
    assert plugin.get_template_spec().template_key == "capacitor_bank_controller"


def test_registry_matches_svg_by_subtype():
    plugin = DeviceMonitorPluginRegistry.resolve(
        _device(device_category="compensation", device_subtype="svg", device_type="svg")
    )

    assert plugin.plugin_key == "svg"
    assert plugin.get_template_spec().template_key == "svg"


def test_registry_matches_storage_by_category():
    plugin = DeviceMonitorPluginRegistry.resolve(
        _device(device_category="storage", device_type="vendor_storage_box")
    )

    assert plugin.plugin_key == "storage"
    assert plugin.get_template_spec().template_key == "storage"


def test_registry_matches_meter_templates_by_category():
    for template_key in ("water_meter", "gas_meter", "heat_meter", "cooling_meter"):
        plugin = DeviceMonitorPluginRegistry.resolve(
            _device(device_category=template_key, device_type=template_key)
        )

        assert plugin.plugin_key == template_key
        assert plugin.get_template_spec().template_key == template_key


def test_registry_falls_back_to_generic_for_unknown_device():
    plugin = DeviceMonitorPluginRegistry.resolve(
        _device(device_category="vendor_box", device_type="vendor_box")
    )

    assert plugin.plugin_key == "generic_device"
    assert plugin.get_template_spec().template_key == "generic_device"


def test_registry_prefers_subtype_over_category():
    plugin = DeviceMonitorPluginRegistry.resolve(
        _device(
            device_category="storage",
            device_subtype="capacitor_bank_controller",
            device_type="compensation",
        )
    )

    assert plugin.plugin_key == "capacitor_bank_controller"


def test_plugin_build_monitor_payload_accepts_context_object():
    device = _device(device_category="vendor_box", device_type="vendor_box")
    plugin = DeviceMonitorPluginRegistry.resolve(device)
    context = DeviceMonitorContext(
        session=None,
        device=device,
        realtime={"flow_rate": 12.5},
        runtime_status={"is_online": True},
        ingestion_health={"status": "online"},
    )

    assert plugin.build_monitor_payload(context) is None
