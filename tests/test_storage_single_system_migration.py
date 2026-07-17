from datetime import date, datetime
from pathlib import Path

from app.models.storage import (
    StorageAssetProfile,
    StorageDispatchPlan,
    StorageTelemetry,
)

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "migrations/versions/20260717_0003_add_storage_source_and_control_gates.py"


def test_single_system_models_keep_source_run_and_device_gate_defaults():
    profile = StorageAssetProfile(device_id=1, rated_energy_kwh=500, rated_power_kw=250)
    telemetry = StorageTelemetry(device_id=1, timestamp=datetime(2026, 7, 17, 12, 0, 0))
    dispatch = StorageDispatchPlan(
        device_id=1,
        dispatch_date=date(2026, 7, 18),
        slot_index=0,
        target_active_power=0,
    )

    assert profile.ems_auto_enabled is False
    assert telemetry.simulation_run_id is None
    assert dispatch.data_source == "calculated"
    assert dispatch.simulation_run_id is None
    assert StorageTelemetry.__table__.c.simulation_run_id.index is True
    assert StorageDispatchPlan.__table__.c.simulation_run_id.index is True


def test_single_system_migration_is_static_additive_and_offline_safe():
    text = MIGRATION.read_text(encoding="utf-8")

    assert 'revision = "20260717_0003"' in text
    assert 'down_revision = "20260716_0002"' in text
    assert "op.get_bind" not in text
    assert "inspect(" not in text
    assert text.count("op.add_column(") == 4
    assert '"storage_asset_profile"' in text
    assert '"ems_auto_enabled"' in text
    assert text.count('"simulation_run_id"') >= 4
    assert '"storage_dispatch_plan"' in text
    assert '"data_source"' in text
    assert "ix_storage_telemetry_simulation_run_id" in text
    assert "ix_storage_dispatch_plan_simulation_run_id" in text
