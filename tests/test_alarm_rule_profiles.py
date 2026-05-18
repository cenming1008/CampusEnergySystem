from app.domain.alarm_rule_profiles import (
    DeviceRuleIdentity,
    resolve_capacitor_bank_profile,
    resolve_generic_threshold_profile,
    resolve_media_threshold_profile,
    resolve_storage_threshold_profile,
)


def test_resolve_generic_threshold_profile_uses_default_category_subtype_device_order():
    profile = resolve_generic_threshold_profile(
        {
            "alarm_rules": {
                "platform_rules": {
                    "generic_thresholds": {
                        "default": {
                            "enabled": True,
                            "current_max": 45.0,
                            "voltage_min": 190.0,
                            "voltage_max": 250.0,
                        },
                        "device_categories": {
                            "load": {
                                "current_max": 30.0,
                                "voltage_min": 185.0,
                            },
                        },
                        "device_subtypes": {
                            "smart_meter": {
                                "current_max": 20.0,
                            },
                        },
                        "devices": {
                            "7": {
                                "current_max": 10.0,
                            },
                        },
                    },
                },
            },
        },
        DeviceRuleIdentity(
            device_id=7,
            device_category="load",
            device_subtype="smart_meter",
        ),
    )

    assert profile.enabled is True
    assert profile.thresholds.current_max == 10.0
    assert profile.thresholds.voltage_min == 185.0
    assert profile.thresholds.voltage_max == 250.0


def test_resolve_generic_threshold_profile_keeps_legacy_settings_shape():
    profile = resolve_generic_threshold_profile(
        {
            "default": {
                "current_max": 45.0,
                "voltage_min": 190.0,
                "voltage_max": 250.0,
            },
            "device_thresholds": {
                "7": {
                    "current_max": 11.0,
                },
            },
        },
        DeviceRuleIdentity(device_id=7, device_category="load"),
    )

    assert profile.enabled is True
    assert profile.thresholds.current_max == 11.0
    assert profile.thresholds.voltage_min == 190.0
    assert profile.thresholds.voltage_max == 250.0


def test_resolve_capacitor_bank_profile_merges_device_profile_and_rule_overrides():
    profile = resolve_capacitor_bank_profile(
        {
            "alarm_rules": {
                "platform_rules": {
                    "capacitor_bank": {
                        "default": {
                            "enabled": True,
                            "temperature_upper_limit": 55.0,
                            "overvoltage_threshold": 245.0,
                        },
                        "devices": {
                            "7": {
                                "temperature_upper_limit": 60.0,
                            },
                        },
                    },
                },
            },
        },
        DeviceRuleIdentity(
            device_id=7,
            device_category="compensation",
            device_subtype="capacitor_bank_controller",
        ),
        {
            "temperature_upper_limit": 50.0,
            "voltage_harmonic_threshold": 4.5,
            "current_harmonic_threshold": 2.8,
        },
    )

    assert profile.platform_rules_enabled is True
    assert profile.thresholds.temperature_upper_limit == 60.0
    assert profile.thresholds.overvoltage_threshold == 245.0
    assert profile.thresholds.voltage_harmonic_threshold == 4.5
    assert profile.thresholds.current_harmonic_threshold == 2.8
    assert profile.thresholds.voltage_harmonic_trigger_margin == 0.0


def test_resolve_capacitor_bank_profile_uses_vendor_aligned_defaults_when_no_device_values():
    profile = resolve_capacitor_bank_profile(
        {
            "alarm_rules": {
                "platform_rules": {
                    "capacitor_bank": {
                        "default": {
                            "enabled": True,
                            "temperature_upper_limit": 65.0,
                            "overvoltage_threshold": 250.0,
                            "voltage_harmonic_threshold": 5.0,
                            "voltage_harmonic_trigger_margin": 0.2,
                            "current_harmonic_threshold": 80.0,
                        },
                    },
                },
            },
        },
        DeviceRuleIdentity(
            device_id=7,
            device_category="compensation",
            device_subtype="capacitor_bank_controller",
        ),
        {},
    )

    assert profile.platform_rules_enabled is True
    assert profile.thresholds.temperature_upper_limit == 65.0
    assert profile.thresholds.overvoltage_threshold == 250.0
    assert profile.thresholds.voltage_harmonic_threshold == 5.0
    assert profile.thresholds.voltage_harmonic_trigger_margin == 0.2
    assert profile.thresholds.current_harmonic_threshold == 80.0


def test_resolve_capacitor_bank_profile_can_disable_platform_rules():
    profile = resolve_capacitor_bank_profile(
        {
            "alarm_rules": {
                "platform_rules": {
                    "capacitor_bank": {
                        "default": {"enabled": False},
                    },
                },
            },
        },
        DeviceRuleIdentity(device_id=7, device_category="compensation"),
        {
            "temperature_upper_limit": 50.0,
        },
    )

    assert profile.platform_rules_enabled is False
    assert profile.thresholds.temperature_upper_limit is None


def test_resolve_media_threshold_profile_uses_category_subtype_device_order():
    profile = resolve_media_threshold_profile(
        {
            "alarm_rules": {
                "platform_rules": {
                    "media_thresholds": {
                        "default": {
                            "enabled": False,
                            "pressure_max": 1.0,
                        },
                        "device_categories": {
                            "water_meter": {
                                "enabled": True,
                                "pressure_max": 0.8,
                                "temperature_max": 60.0,
                            },
                        },
                        "device_subtypes": {
                            "cold_water_meter": {
                                "temperature_max": 35.0,
                            },
                        },
                        "devices": {
                            "7": {
                                "pressure_max": 0.6,
                            },
                        },
                    },
                },
            },
        },
        DeviceRuleIdentity(
            device_id=7,
            device_category="water_meter",
            device_subtype="cold_water_meter",
        ),
    )

    assert profile.enabled is True
    assert profile.thresholds.pressure_max == 0.6
    assert profile.thresholds.temperature_max == 35.0
    assert profile.thresholds.flow_rate_max is None


def test_resolve_storage_threshold_profile_uses_category_subtype_device_order():
    profile = resolve_storage_threshold_profile(
        {
            "alarm_rules": {
                "platform_rules": {
                    "storage": {
                        "default": {
                            "enabled": False,
                            "soc_min": 15.0,
                            "cell_temp_max": 55.0,
                        },
                        "device_categories": {
                            "storage": {
                                "enabled": True,
                                "soc_min": 20.0,
                                "soh_min": 80.0,
                            },
                        },
                        "device_subtypes": {
                            "battery_cabinet": {
                                "cell_temp_max": 50.0,
                            },
                        },
                        "devices": {
                            "7": {
                                "soc_min": 25.0,
                            },
                        },
                    },
                },
            },
        },
        DeviceRuleIdentity(
            device_id=7,
            device_category="storage",
            device_subtype="battery_cabinet",
        ),
    )

    assert profile.enabled is True
    assert profile.thresholds.soc_min == 25.0
    assert profile.thresholds.soh_min == 80.0
    assert profile.thresholds.cell_temp_max == 50.0
