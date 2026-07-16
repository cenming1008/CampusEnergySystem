import ast
from pathlib import Path

from app.models.tables import SQLModel

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

LEGACY_FILES = {
    "20260325_0001_industrial_baseline.py",
    "20260325_0002_mqtt_retry_dead_letter.py",
    "20260412_0003_add_reactive_power.py",
    "20260412_0004_add_svg_tables.py",
    "20260412_0005_merge_svg_operations_profile.py",
    "20260414_0006_unify_compensation_type_to_svg.py",
    "20260414_0007_add_device_subtype.py",
    "20260423_0008_drop_prediction.py",
    "20260424_0009_add_capacitor_bank_monitor_fields.py",
    "20260424_0010_add_device_archive_status.py",
    "20260515_0011_add_capacitor_bank_harmonic_spectrum.py",
}

RUNTIME_INDEXES = {
    "idx_energydata_device_timestamp": ("energydata", ("device_id", "timestamp DESC")),
    "idx_energydata_energy_type_timestamp": (
        "energydata",
        ("energy_type", "timestamp DESC"),
    ),
    "idx_alarm_device_resolved_timestamp": (
        "alarm",
        ("device_id", "is_resolved", "timestamp DESC"),
    ),
    "idx_alarm_instance_recovered_last_seen": (
        "alarm",
        ("instance_key", "recovered_at", "last_seen_at DESC"),
    ),
    "idx_device_ingestion_health_last_success": (
        "device_ingestion_health",
        ("last_success_at DESC",),
    ),
    "idx_device_ingestion_health_last_failure": (
        "device_ingestion_health",
        ("last_failure_at DESC",),
    ),
    "idx_audit_event_action_created_at": (
        "audit_event",
        ("action", "created_at DESC"),
    ),
    "idx_audit_event_actor_created_at": (
        "audit_event",
        ("actor", "created_at DESC"),
    ),
    "idx_audit_event_outcome_created_at": (
        "audit_event",
        ("outcome", "created_at DESC"),
    ),
    "idx_mqtt_ingestion_record_device_received": (
        "mqtt_ingestion_record",
        ("device_id", "received_at DESC"),
    ),
    "idx_mqtt_ingestion_record_status_received": (
        "mqtt_ingestion_record",
        ("status", "received_at DESC"),
    ),
    "idx_mqtt_ingestion_record_next_retry_at": (
        "mqtt_ingestion_record",
        ("next_retry_at",),
    ),
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
    tree = ast.parse(text)
    forbidden = [
        "SQLModel",
        ".metadata",
        "information_schema",
    ]
    for token in forbidden:
        assert token not in text
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(
                alias.name != "app" and not alias.name.startswith("app.")
                for alias in node.names
            )
        if isinstance(node, ast.ImportFrom):
            assert node.module != "app" and not (node.module or "").startswith("app.")
        if isinstance(node, ast.Call):
            assert not (isinstance(node.func, ast.Name) and node.func.id == "inspect")
            assert not (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in {"get_bind", "fetchone"}
            )
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
    files = {path.name for path in ARCHIVE.glob("*.py")}
    assert files == LEGACY_FILES
    readme = (ARCHIVE / "README.md").read_text(encoding="utf-8")
    for revision in LEGACY_REVISIONS:
        assert revision in readme
    assert readme.count("superseded by `20260716_0001`") == 11


def _literal_string(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "sa"
        and node.func.attr == "text"
    ):
        return ast.literal_eval(node.args[0])
    raise AssertionError(f"expected a literal index column, got {ast.dump(node)}")


def test_baseline_includes_all_runtime_query_indexes_with_exact_ordering():
    baseline = ACTIVE / "20260716_0001_campus_baseline.py"
    tree = ast.parse(baseline.read_text(encoding="utf-8"))
    actual = {}
    dropped = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if not isinstance(node.func.value, ast.Name) or node.func.value.id != "op":
            continue
        if node.func.attr == "create_index" and isinstance(node.args[0], ast.Constant):
            name = ast.literal_eval(node.args[0])
            if name in RUNTIME_INDEXES:
                table = ast.literal_eval(node.args[1])
                columns = tuple(_literal_string(column) for column in node.args[2].elts)
                actual[name] = (table, columns)
        if node.func.attr == "drop_index" and isinstance(node.args[0], ast.Constant):
            dropped.add(ast.literal_eval(node.args[0]))

    assert actual == RUNTIME_INDEXES
    assert dropped >= RUNTIME_INDEXES.keys()


def test_model_metadata_includes_all_runtime_query_indexes_with_exact_ordering():
    actual = {}
    for name, (table_name, _) in RUNTIME_INDEXES.items():
        table = SQLModel.metadata.tables[table_name]
        index = next((candidate for candidate in table.indexes if candidate.name == name), None)
        if index is None:
            continue
        columns = tuple(
            expression.name
            if getattr(expression, "name", None) is not None
            else str(expression.compile())
            for expression in index.expressions
        )
        actual[name] = (table_name, columns)

    assert actual == RUNTIME_INDEXES
