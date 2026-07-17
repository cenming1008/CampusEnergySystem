from datetime import date, datetime

from sqlalchemy import UniqueConstraint

from app.models.storage import (
    StorageAssetProfile,
    StorageDispatchPlan,
    StorageTelemetry,
)


def test_storage_contract_models_keep_power_direction_and_source():
    profile = StorageAssetProfile(
        device_id=1,
        rated_energy_kwh=500,
        rated_power_kw=250,
        soc_min=10,
        soc_max=90,
    )
    telemetry = StorageTelemetry(
        device_id=1,
        timestamp=datetime(2026, 7, 16),
        target_active_power=-125,
        data_source="simulated",
    )
    plan = StorageDispatchPlan(
        device_id=1,
        dispatch_date=date(2026, 7, 17),
        slot_index=0,
        target_active_power=100,
        strategy="day_ahead",
    )

    assert profile.rated_energy_kwh == 500
    assert telemetry.target_active_power == -125
    assert telemetry.data_source == "simulated"
    assert plan.slot_index == 0


def test_storage_asset_profile_exposes_approved_asset_fields():
    columns = set(StorageAssetProfile.__table__.columns.keys())

    assert columns == {
        "device_id",
        "rated_energy_kwh",
        "rated_power_kw",
        "max_charge_power_kw",
        "max_discharge_power_kw",
        "charge_efficiency",
        "discharge_efficiency",
        "soc_min",
        "soc_max",
        "soc_soft_min",
        "soc_soft_max",
        "rated_ac_voltage",
        "rated_dc_voltage",
        "battery_type",
        "bms_model",
        "pcs_model",
        "protocol_version",
        "installation_location",
        "commission_date",
        "data_source",
        "ems_auto_enabled",
        "created_at",
        "updated_at",
    }
    assert StorageAssetProfile.__table__.c.device_id.primary_key


def test_storage_telemetry_adds_exactly_the_approved_control_fields():
    approved = {
        "target_active_power",
        "available_charge_power",
        "available_discharge_power",
        "bms_status",
        "pcs_status",
        "grid_status",
        "command_source",
        "data_source",
        "simulation_run_id",
    }

    assert approved <= set(StorageTelemetry.__table__.columns.keys())
    telemetry = StorageTelemetry(device_id=1, timestamp=datetime(2026, 7, 16))
    assert telemetry.data_source == "telemetry"


def test_storage_dispatch_plan_has_unique_device_date_slot_contract():
    columns = set(StorageDispatchPlan.__table__.columns.keys())
    unique_column_sets = {
        tuple(constraint.columns.keys())
        for constraint in StorageDispatchPlan.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert columns == {
        "id",
        "device_id",
        "dispatch_date",
        "slot_index",
        "interval_minutes",
        "target_active_power",
        "forecast_load_power",
        "forecast_pv_power",
        "tariff_price",
        "expected_soc",
        "strategy",
        "strategy_version",
        "solver_status",
        "is_valid",
        "failure_reason",
        "generated_at",
        "data_source",
        "simulation_run_id",
    }
    assert ("device_id", "dispatch_date", "slot_index") in unique_column_sets
