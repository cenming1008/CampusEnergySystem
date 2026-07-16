from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "migrations" / "versions"
ARCHIVE = ROOT / "docs" / "archive" / "migrations" / "legacy-pre-20260716"

LEGACY_REVISIONS = {
    "20260325_0001",
    "20260325_0002",
    "20260412_0003",
    "20260412_0004",
    "20260412_0005",
    "20260414_0006",
    "20260414_0007",
    "20260423_0008",
    "20260424_0009",
    "20260424_0010",
    "20260515_0011",
}

REQUIRED_TABLES = {
    "alarm",
    "audit_event",
    "capacitor_bank_control_profile",
    "capacitor_bank_telemetry",
    "carbon_emission",
    "device",
    "device_control_log",
    "device_group",
    "device_group_membership",
    "device_ingestion_health",
    "device_maintenance",
    "energy_statistics",
    "energydata",
    "inspection_plan",
    "inspection_point",
    "inspection_record",
    "inspection_route",
    "inspection_task",
    "location",
    "mqtt_ingestion_record",
    "storage_telemetry",
    "svg_asset_profile",
    "svg_config",
    "svg_telemetry",
    "user",
}


def test_only_static_root_is_active():
    files = sorted(path.name for path in ACTIVE.glob("*.py") if path.name != "__init__.py")
    assert files == ["20260716_0001_campus_baseline.py"]


def test_baseline_is_offline_safe_and_static():
    text = (ACTIVE / "20260716_0001_campus_baseline.py").read_text(encoding="utf-8")
    forbidden = [
        "SQLModel",
        ".metadata",
        "op.get_bind",
        "inspect(",
        "fetchone",
        "information_schema",
        "from app",
    ]
    for token in forbidden:
        assert token not in text
    assert 'revision = "20260716_0001"' in text
    assert "down_revision = None" in text
    assert text.count("op.create_table(") == len(REQUIRED_TABLES)
    for table in REQUIRED_TABLES:
        assert f'"{table}"' in text
    assert "CREATE EXTENSION IF NOT EXISTS timescaledb" in text
    assert "create_hypertable" in text
    assert text.index("CREATE EXTENSION IF NOT EXISTS timescaledb") < text.index("op.create_table(")
    assert text.index('op.create_table(\n        "energydata"') < text.index("create_hypertable")
    assert "drop extension" not in text.lower()


def test_archive_contains_the_complete_superseded_chain():
    files = sorted(path.name for path in ARCHIVE.glob("*.py"))
    assert len(files) == 11
    readme = (ARCHIVE / "README.md").read_text(encoding="utf-8")
    for revision in LEGACY_REVISIONS:
        assert revision in readme
    assert readme.count("superseded by `20260716_0001`") == 11
