import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = (
    ROOT
    / "migrations"
    / "versions"
    / "20260716_0002_add_storage_simulation_contracts.py"
)

APPROVED_TABLES = {
    "storage_asset_profile",
    "storage_dispatch_plan",
}
APPROVED_TELEMETRY_COLUMNS = {
    "target_active_power",
    "available_charge_power",
    "available_discharge_power",
    "bms_status",
    "pcs_status",
    "grid_status",
    "command_source",
    "data_source",
}


def _migration_tree() -> tuple[str, ast.Module]:
    text = MIGRATION.read_text(encoding="utf-8")
    return text, ast.parse(text)


def _op_calls(tree: ast.Module, operation: str) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "op"
        and node.func.attr == operation
    ]


def test_storage_migration_has_fixed_revision_and_is_offline_safe():
    text, tree = _migration_tree()

    assert 'revision = "20260716_0002"' in text
    assert 'down_revision = "20260716_0001"' in text
    assert "SQLModel" not in text
    assert ".metadata" not in text
    assert "information_schema" not in text

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(
                alias.name != "app" and not alias.name.startswith("app.")
                for alias in node.names
            )
        if isinstance(node, ast.ImportFrom):
            assert node.module != "app" and not (node.module or "").startswith("app.")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"get_bind", "execute", "fetchone"}


def test_storage_migration_creates_only_approved_tables_and_extensions():
    _, tree = _migration_tree()

    created_tables = {
        ast.literal_eval(call.args[0]) for call in _op_calls(tree, "create_table")
    }
    added_columns = {
        ast.literal_eval(call.args[1].args[0])
        for call in _op_calls(tree, "add_column")
        if ast.literal_eval(call.args[0]) == "storage_telemetry"
    }

    assert created_tables == APPROVED_TABLES
    assert "storage_telemetry" not in created_tables
    assert added_columns == APPROVED_TELEMETRY_COLUMNS


def test_storage_migration_downgrade_removes_only_task3_additions():
    text, tree = _migration_tree()

    dropped_tables = {
        ast.literal_eval(call.args[0]) for call in _op_calls(tree, "drop_table")
    }
    dropped_columns = {
        ast.literal_eval(call.args[1])
        for call in _op_calls(tree, "drop_column")
        if ast.literal_eval(call.args[0]) == "storage_telemetry"
    }

    assert dropped_tables == APPROVED_TABLES
    assert 'op.drop_table("storage_telemetry")' not in text
    assert dropped_columns == APPROVED_TELEMETRY_COLUMNS

