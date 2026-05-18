"""Alarm rule profile resolution.

This module keeps rule configuration merging separate from alarm lifecycle logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from app.domain.alarm_rules import CapacitorThresholds, MediaThresholds, StorageThresholds, ThresholdConfig


@dataclass(frozen=True)
class DeviceRuleIdentity:
    """Device attributes used when resolving alarm rules."""

    device_id: int
    device_category: Optional[str] = None
    device_subtype: Optional[str] = None


@dataclass(frozen=True)
class GenericThresholdProfile:
    """Resolved generic threshold rule profile for one device."""

    enabled: bool
    thresholds: ThresholdConfig


@dataclass(frozen=True)
class CapacitorBankRuleProfile:
    """Resolved capacitor-bank platform rule profile for one device."""

    platform_rules_enabled: bool
    thresholds: CapacitorThresholds


@dataclass(frozen=True)
class MediaThresholdProfile:
    """Resolved media threshold rule profile for one device."""

    enabled: bool
    thresholds: MediaThresholds


@dataclass(frozen=True)
class StorageThresholdProfile:
    """Resolved storage threshold rule profile for one device."""

    enabled: bool
    thresholds: StorageThresholds


def resolve_generic_threshold_profile(
    raw_config: dict[str, Any],
    identity: DeviceRuleIdentity,
) -> GenericThresholdProfile:
    """Resolve generic voltage/current threshold config for a device.

    Supports the current legacy shape:
    {
        "default": {"current_max": 45},
        "device_thresholds": {"1": {"current_max": 10}}
    }

    And the staged unified-rule shape:
    {
        "alarm_rules": {
            "platform_rules": {
                "generic_thresholds": {
                    "default": {"enabled": true, "current_max": 45},
                    "device_categories": {"load": {"current_max": 20}},
                    "device_subtypes": {"meter": {"current_max": 15}},
                    "devices": {"1": {"current_max": 10}}
                }
            }
        }
    }
    """

    raw_config = raw_config or {}
    generic_rules = (
        raw_config
        .get("alarm_rules", {})
        .get("platform_rules", {})
        .get("generic_thresholds")
    )
    if isinstance(generic_rules, dict):
        merged = _merge_profiles(
            generic_rules.get("default"),
            _lookup_profile(generic_rules.get("device_categories"), identity.device_category),
            _lookup_profile(generic_rules.get("device_subtypes"), identity.device_subtype),
            _lookup_profile(generic_rules.get("devices"), str(identity.device_id)),
        )
        return _profile_from_mapping(merged)

    legacy_default = raw_config.get("default", {})
    legacy_device = raw_config.get("device_thresholds", {}).get(str(identity.device_id), {})
    merged = _merge_profiles(legacy_default, legacy_device)
    return _profile_from_mapping(merged)


def resolve_capacitor_bank_profile(
    raw_config: dict[str, Any],
    identity: DeviceRuleIdentity,
    device_profile: Optional[dict[str, Any]] = None,
) -> CapacitorBankRuleProfile:
    """Resolve capacitor-bank platform rule thresholds for a device."""

    raw_config = raw_config or {}
    capacitor_rules = (
        raw_config
        .get("alarm_rules", {})
        .get("platform_rules", {})
        .get("capacitor_bank")
    )

    if isinstance(capacitor_rules, dict):
        merged = _merge_profiles(
            capacitor_rules.get("default"),
            device_profile,
            _lookup_profile(capacitor_rules.get("device_categories"), identity.device_category),
            _lookup_profile(capacitor_rules.get("device_subtypes"), identity.device_subtype),
            _lookup_profile(capacitor_rules.get("devices"), str(identity.device_id)),
        )
    else:
        merged = _merge_profiles(device_profile)

    enabled = bool(merged.get("enabled", True))
    if not enabled:
        return CapacitorBankRuleProfile(
            platform_rules_enabled=False,
            thresholds=CapacitorThresholds(),
        )

    return CapacitorBankRuleProfile(
        platform_rules_enabled=True,
        thresholds=CapacitorThresholds(
            temperature_upper_limit=_to_optional_float(merged.get("temperature_upper_limit")),
            overvoltage_threshold=_to_optional_float(merged.get("overvoltage_threshold")),
            voltage_harmonic_threshold=_to_optional_float(merged.get("voltage_harmonic_threshold")),
            voltage_harmonic_trigger_margin=_to_float(merged.get("voltage_harmonic_trigger_margin"), 0.0),
            current_harmonic_threshold=_to_optional_float(merged.get("current_harmonic_threshold")),
        ),
    )


def resolve_media_threshold_profile(
    raw_config: dict[str, Any],
    identity: DeviceRuleIdentity,
) -> MediaThresholdProfile:
    """Resolve shared media-meter thresholds for flow, pressure and temperature."""

    raw_config = raw_config or {}
    media_rules = (
        raw_config
        .get("alarm_rules", {})
        .get("platform_rules", {})
        .get("media_thresholds")
    )
    if not isinstance(media_rules, dict):
        return MediaThresholdProfile(enabled=False, thresholds=MediaThresholds())

    merged = _merge_profiles(
        media_rules.get("default"),
        _lookup_profile(media_rules.get("device_categories"), identity.device_category),
        _lookup_profile(media_rules.get("device_subtypes"), identity.device_subtype),
        _lookup_profile(media_rules.get("devices"), str(identity.device_id)),
    )
    if not bool(merged.get("enabled", False)):
        return MediaThresholdProfile(enabled=False, thresholds=MediaThresholds())

    return MediaThresholdProfile(
        enabled=True,
        thresholds=MediaThresholds(
            flow_rate_min=_to_optional_float(merged.get("flow_rate_min")),
            flow_rate_max=_to_optional_float(merged.get("flow_rate_max")),
            pressure_min=_to_optional_float(merged.get("pressure_min")),
            pressure_max=_to_optional_float(merged.get("pressure_max")),
            temperature_min=_to_optional_float(merged.get("temperature_min")),
            temperature_max=_to_optional_float(merged.get("temperature_max")),
        ),
    )


def resolve_storage_threshold_profile(
    raw_config: dict[str, Any],
    identity: DeviceRuleIdentity,
) -> StorageThresholdProfile:
    """Resolve storage thresholds for SOC, SOH, temperature and power."""

    raw_config = raw_config or {}
    storage_rules = (
        raw_config
        .get("alarm_rules", {})
        .get("platform_rules", {})
        .get("storage")
    )
    if not isinstance(storage_rules, dict):
        return StorageThresholdProfile(enabled=False, thresholds=StorageThresholds())

    merged = _merge_profiles(
        storage_rules.get("default"),
        _lookup_profile(storage_rules.get("device_categories"), identity.device_category),
        _lookup_profile(storage_rules.get("device_subtypes"), identity.device_subtype),
        _lookup_profile(storage_rules.get("devices"), str(identity.device_id)),
    )
    if not bool(merged.get("enabled", False)):
        return StorageThresholdProfile(enabled=False, thresholds=StorageThresholds())

    return StorageThresholdProfile(
        enabled=True,
        thresholds=StorageThresholds(
            soc_min=_to_optional_float(merged.get("soc_min")),
            soc_max=_to_optional_float(merged.get("soc_max")),
            soh_min=_to_optional_float(merged.get("soh_min")),
            cell_temp_max=_to_optional_float(merged.get("cell_temp_max")),
            active_power_abs_max=_to_optional_float(merged.get("active_power_abs_max")),
        ),
    )


def _lookup_profile(profiles: Any, key: Optional[str]) -> dict[str, Any]:
    if not key or not isinstance(profiles, dict):
        return {}
    profile = profiles.get(key)
    return profile if isinstance(profile, dict) else {}


def _merge_profiles(*profiles: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for profile in profiles:
        if isinstance(profile, dict):
            merged.update(profile)
    return merged


def _profile_from_mapping(profile: dict[str, Any]) -> GenericThresholdProfile:
    return GenericThresholdProfile(
        enabled=bool(profile.get("enabled", True)),
        thresholds=ThresholdConfig(
            current_max=_to_float(profile.get("current_max"), 45.0),
            voltage_max=_to_float(profile.get("voltage_max"), 250.0),
            voltage_min=_to_float(profile.get("voltage_min"), 190.0),
        ),
    )


def _to_float(value: Any, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
